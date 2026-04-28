"""
Менеджер контекста диалогов.
Хранение истории сообщений в памяти для каждого пользователя.
"""

import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from collections import defaultdict

from config import config

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Сообщение в истории чата."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str


class DialogContext:
    """Контекст диалога для одного пользователя."""

    def __init__(self, user_id: int, max_length: int = None):
        self.user_id = user_id
        self.max_length = max_length or config.MAX_CONTEXT_LENGTH
        self.messages: list[Message] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Настройки модели и температуры
        self.model: str = config.MODEL
        self.temperature: float = config.DEFAULT_TEMPERATURE
        
        # Добавляем системный промпт
        self._add_system_message()
        logger.info(f"Создан контекст для пользователя {user_id}")

    def _add_system_message(self) -> None:
        """Добавить системное сообщение."""
        self.messages.append(Message(
            role="system",
            content=config.SYSTEM_PROMPT,
            timestamp=datetime.now().isoformat()
        ))

    def add_message(self, role: str, content: str) -> None:
        """Добавить сообщение в историю."""
        self.messages.append(Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        ))
        self.last_activity = datetime.now()
        
        # Очищаем старые сообщения, если превышен лимит
        self._trim_history()
        logger.debug(f"Добавлено сообщение ({role}) для пользователя {self.user_id}")

    def _trim_history(self) -> None:
        """Удалить старые сообщения, оставляя системный промпт и последние N сообщений."""
        if len(self.messages) <= self.max_length:
            return
        
        # Сохраняем системное сообщение
        system_msg = self.messages[0] if self.messages[0].role == "system" else None
        
        # Оставляем последние max_length - 1 сообщений (плюс системное)
        keep_count = self.max_length - 1 if system_msg else self.max_length
        self.messages = [system_msg] + self.messages[-keep_count:] if system_msg else self.messages[-keep_count:]
        
        logger.debug(f"История обрезана до {len(self.messages)} сообщений для пользователя {self.user_id}")

    def clear(self) -> None:
        """Очистить историю, сохраняя системный промпт."""
        system_msg = None
        if self.messages and self.messages[0].role == "system":
            system_msg = self.messages[0]
        
        self.messages = [system_msg] if system_msg else []
        self._add_system_message() if not system_msg else None
        self.last_activity = datetime.now()
        logger.info(f"Контекст очищен для пользователя {self.user_id}")

    def get_messages(self) -> list[dict]:
        """Получить сообщения в формате для API."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def get_messages_without_system(self) -> list[dict]:
        """Получить сообщения без системного промпта."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages if msg.role != "system"]

    @property
    def message_count(self) -> int:
        """Количество сообщений (без системного)."""
        return len([m for m in self.messages if m.role != "system"])

    def set_temperature(self, temperature: float) -> None:
        """Установить температуру генерации."""
        self.temperature = max(0.0, min(1.0, temperature))
        self.last_activity = datetime.now()
        logger.info(f"Температура для пользователя {self.user_id} установлена в {self.temperature}")

    def set_model(self, model: str) -> None:
        """Установить модель."""
        self.model = model
        self.last_activity = datetime.now()
        logger.info(f"Модель для пользователя {self.user_id} установлена в {self.model}")


class ContextManager:
    """Управление контекстами всех пользователей."""

    def __init__(self):
        self._contexts: dict[int, DialogContext] = {}
        logger.info("ContextManager инициализирован")

    def get_context(self, user_id: int) -> DialogContext:
        """Получить или создать контекст для пользователя."""
        if user_id not in self._contexts:
            self._contexts[user_id] = DialogContext(user_id)
        return self._contexts[user_id]

    def clear_context(self, user_id: int) -> bool:
        """Очистить контекст пользователя."""
        if user_id in self._contexts:
            self._contexts[user_id].clear()
            logger.info(f"Контекст пользователя {user_id} очищен")
            return True
        return False

    def delete_context(self, user_id: int) -> bool:
        """Удалить контекст пользователя."""
        if user_id in self._contexts:
            del self._contexts[user_id]
            logger.info(f"Контекст пользователя {user_id} удалён")
            return True
        return False

    def get_stats(self) -> dict:
        """Получить статистику по всем контекстам."""
        return {
            "active_users": len(self._contexts),
            "total_messages": sum(ctx.message_count for ctx in self._contexts.values())
        }

    def cleanup_inactive(self, max_inactive_hours: int = 24) -> int:
        """Удалить контексты неактивных пользователей."""
        now = datetime.now()
        removed = 0
        
        inactive_users = [
            user_id for user_id, ctx in self._contexts.items()
            if (now - ctx.last_activity).total_seconds() > max_inactive_hours * 3600
        ]
        
        for user_id in inactive_users:
            self.delete_context(user_id)
            removed += 1
        
        if removed > 0:
            logger.info(f"Удалено {removed} неактивных контекстов")
        
        return removed


# Глобальный экземпляр менеджера контекстов
context_manager = ContextManager()
