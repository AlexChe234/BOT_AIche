"""
Клиент для работы с AI моделями через ProxyApi.ru.
Поддержка OpenAI-совместимых и Anthropic моделей.
"""

import logging
import time
from typing import Optional
from dataclasses import dataclass

import httpx
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError
from anthropic import Anthropic, APIError as AnthropicAPIError

from config import config

logger = logging.getLogger(__name__)
error_logger = logging.getLogger("bot.errors")


@dataclass
class AIResponse:
    """Ответ от AI модели."""
    content: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    thinking: Optional[str] = None
    thinking_tokens: Optional[int] = None


class ProxyAPIClient:
    """Клиент для работы с ProxyApi.ru."""

    def __init__(self):
        self.api_key = config.PROXYAPI_KEY
        self.model = config.MODEL
        self.timeout = config.REQUEST_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        
        # Определяем тип клиента по модели
        self._is_anthropic = self.model.startswith("claude")
        
        if self._is_anthropic:
            self.client = Anthropic(
                api_key=self.api_key,
                base_url="https://api.proxyapi.ru/anthropic",
                timeout=httpx.Timeout(self.timeout)
            )
            logger.info(f"Инициализирован Anthropic клиент: {self.model}")
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.proxyapi.ru/openai/v1",
                timeout=httpx.Timeout(self.timeout)
            )
            logger.info(f"Инициализирован OpenAI клиент: {self.model}")

    def send_message(self, messages: list[dict]) -> AIResponse:
        """
        Отправить сообщения и получить ответ.
        
        Args:
            messages: Список сообщений в формате [{"role": "...", "content": "..."}]
        
        Returns:
            AIResponse с ответом модели
        """
        # Логируем отправляемые параметры (без чувствительных данных)
        logger.info(f"Отправка запроса к {self.model}")
        logger.debug(f"Количество сообщений: {len(messages)}")
        logger.debug(f"Сообщения: {self._safe_log_messages(messages)}")

        for attempt in range(self.max_retries):
            try:
                if self._is_anthropic:
                    response = self._send_anthropic(messages)
                else:
                    response = self._send_openai(messages)
                
                logger.info(
                    f"Ответ получен: {response.input_tokens}in / {response.output_tokens}out токенов"
                )
                return response

            except (APITimeoutError, AnthropicAPIError) as e:
                if "timeout" in str(e).lower() or isinstance(e, APITimeoutError):
                    logger.warning(f"Таймаут запроса (попытка {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                error_logger.error(f"Ошибка API: {e}")
                raise

            except RateLimitError as e:
                logger.warning(f"Превышен лимит запросов: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * 5)
                    continue
                error_logger.error(f"Rate limit: {e}")
                raise RuntimeError("Превышен лимит запросов. Попробуйте позже.")

            except APIConnectionError as e:
                logger.error(f"Ошибка соединения: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                error_logger.error(f"Connection error: {e}")
                raise ConnectionError("Не удалось подключиться к API")

            except APIError as e:
                error_msg = e.message if hasattr(e, 'message') else str(e)
                error_logger.error(f"Ошибка API: {error_msg}")
                raise RuntimeError(f"Ошибка API: {error_msg}")

            except Exception as e:
                error_logger.exception(f"Неожиданная ошибка: {e}")
                raise

        raise RuntimeError("Превышено количество попыток запроса")

    def _send_openai(self, messages: list[dict]) -> AIResponse:
        """Отправить запрос к OpenAI-совместимому API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens if response.usage else None
        output_tokens = response.usage.completion_tokens if response.usage else None

        return AIResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def _send_anthropic(self, messages: list[dict]) -> AIResponse:
        """Отправить запрос к Anthropic API с extended thinking."""
        # Разделяем системное сообщение и остальные
        system_prompt = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)

        request_params = {
            "model": self.model,
            "max_tokens": 16384,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 4096
            },
            "messages": chat_messages
        }

        if system_prompt:
            request_params["system"] = system_prompt

        response = self.client.messages.create(**request_params)

        # Извлекаем thinking и текст ответа
        thinking_text = None
        thinking_tokens = None
        content_text = None

        for block in response.content:
            if hasattr(block, 'type'):
                if block.type == "thinking":
                    thinking_text = block.thinking if hasattr(block, 'thinking') else str(block)
                    thinking_tokens = getattr(block, 'thinking_tokens', None)
                elif block.type == "text":
                    content_text = block.text

        if not content_text:
            content_text = str(response.content[0])

        input_tokens = response.usage.input_tokens if response.usage else None
        output_tokens = response.usage.output_tokens if response.usage else None

        return AIResponse(
            content=content_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking=thinking_text,
            thinking_tokens=thinking_tokens
        )

    def _safe_log_messages(self, messages: list[dict]) -> str:
        """Безопасное логирование сообщений (без токенов)."""
        summary = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            summary.append(f"{role}: {content}")
        return " | ".join(summary)


# Глобальный экземпляр клиента
api_client = ProxyAPIClient()
