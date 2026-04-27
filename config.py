"""
Конфигурация Telegram-бота.
Загрузка переменных окружения и настройки.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# =============================================================================
# Логирование
# =============================================================================

# Создаём директорию для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Отдельный логгер для ошибок
error_logger = logging.getLogger("bot.errors")
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(LOG_DIR / "errors.log", encoding="utf-8")
error_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
error_logger.addHandler(error_handler)

# =============================================================================
# Конфигурация бота
# =============================================================================

class Config:
    """Конфигурация приложения."""
    
    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # ProxyAPI ключ
    PROXYAPI_KEY: str = os.getenv("PROXYAPI_KEY", "")
    
    # Модель для использования
    MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    
    # Таймаут запросов (секунды)
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
    
    # Максимальное количество попыток
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Задержка между попытками (секунды)
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "2"))
    
    # Максимальная длина контекста (сообщений)
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "20"))
    
    # Системный промпт
    SYSTEM_PROMPT: str = os.getenv(
        "SYSTEM_PROMPT",
        "Ты полезный ассистент Telegram-бота. Отвечай кратко и по делу на русском языке."
    )
    
    @classmethod
    def validate(cls) -> bool:
        """Проверить наличие обязательных настроек."""
        if not cls.BOT_TOKEN:
            logger.error("Отсутствует TELEGRAM_BOT_TOKEN в .env")
            return False
        if not cls.PROXYAPI_KEY:
            logger.error("Отсутствует PROXYAPI_KEY в .env")
            return False
        logger.info("Конфигурация проверена успешно")
        return True


# Глобальный экземпляр конфигурации
config = Config()
