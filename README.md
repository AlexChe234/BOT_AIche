# Telegram AI Bot с ProxyApi.ru

Мини-бот Telegram с AI-ассистентом на базе **aiogram 3.x** и **ProxyApi.ru**. Поддерживает контекст диалога, работу с OpenAI-совместимыми и Anthropic моделями.

## 📋 Возможности

- ✅ Контекст диалога в памяти (для каждого пользователя)
- ✅ Поддержка OpenAI-совместимых моделей (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
- ✅ Поддержка Anthropic моделей с Extended Thinking (Claude 4.5 Sonnet)
- ✅ Команда `/reset` для очистки контекста
- ✅ Логирование ошибок и отправляемых параметров
- ✅ Автоматическая очистка неактивных сессий
- ✅ Retry-логика при ошибках API

## 📁 Структура проекта

```
.
├── bot.py              # Основной файл бота (aiogram handlers)
├── config.py           # Конфигурация и переменные окружения
├── context_manager.py  # Управление контекстом диалогов
├── api_client.py       # Клиент для работы с ProxyApi.ru
├── chat_client.py      # CLI клиент (legacy)
├── .env                # Переменные окружения (не в git)
├── .env.example        # Пример конфигурации
├── requirements.txt    # Зависимости Python
├── logs/               # Директория для логов
│   ├── bot.log
│   └── errors.log
└── README.md
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Отредактируйте `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
PROXYAPI_KEY=your_proxyapi_key
AI_MODEL=gpt-4o-mini
```

### 3. Запуск бота

```bash
python bot.py
```

## 📖 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота, приветствие |
| `/reset` | Очистить историю переписки |
| `/stats` | Показать статистику сессии |
| `/help`  | Справка по командам |

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | — |
| `PROXYAPI_KEY` | API ключ ProxyApi.ru | — |
| `AI_MODEL` | Модель AI | `gpt-4o-mini` |
| `REQUEST_TIMEOUT` | Таймаут запроса (сек) | `120` |
| `MAX_RETRIES` | Макс. попыток запроса | `3` |
| `RETRY_DELAY` | Задержка между попытками (сек) | `2` |
| `MAX_CONTEXT_LENGTH` | Макс. сообщений в контексте | `20` |
| `SYSTEM_PROMPT` | Системный промпт | См. `.env.example` |

### Доступные модели

**OpenAI-совместимые:**
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`

**Anthropic (с Extended Thinking):**
- `claude-sonnet-4-5`
- `claude-3-opus`
- `claude-3-haiku`

## 🔑 Получение API ключа

1. Зарегистрируйтесь на [proxyapi.ru](https://console.proxyapi.ru/)
2. Перейдите в раздел **Ключи API**
3. Создайте новый ключ и сохраните его

## 🤖 Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите токен
4. Сохраните токен в `.env` как `TELEGRAM_BOT_TOKEN`

## 📝 Логирование

Бот создаёт два лог-файла в директории `logs/`:

- `bot.log` — общая информация (старт, сообщения пользователей, ответы API)
- `errors.log` — только ошибки (для быстрой диагностики)

Пример лога:
```
2025-01-15 10:30:45 | INFO     | bot | Пользователь john (123456789) запустил бота
2025-01-15 10:30:50 | INFO     | bot | Сообщение от john (123456789): Привет, как дела?...
2025-01-15 10:30:52 | INFO     | bot | Ответ отправлен пользователю john (123456789)
```

## 🔧 Расширение функциональности

### Добавление новых команд

Откройте `bot.py` и добавьте новый handler:

```python
@dp.message(Command("custom"))
async def cmd_custom(message: Message) -> None:
    await message.answer("Ваш кастомный ответ")
```

### Изменение системного промпта

В `.env`:
```env
SYSTEM_PROMPT=Ты опытный программист на Python. Отвечай с примерами кода.
```

### Настройка длины контекста

Для более длинной истории увеличьте `MAX_CONTEXT_LENGTH`:
```env
MAX_CONTEXT_LENGTH=50
```

## 🐛 Диагностика проблем

### Бот не запускается

1. Проверьте `.env` файл — все ли переменные заполнены
2. Убедитесь, что токены действительны
3. Проверьте логи в `logs/errors.log`

### Ошибки API

- `TimeoutError` — увеличьте `REQUEST_TIMEOUT`
- `RateLimitError` — уменьшите количество запросов или увеличьте `RETRY_DELAY`
- `ConnectionError` — проверьте подключение к интернету

### Контекст не сохраняется

Контекст хранится в памяти и сбрасывается при перезапуске бота. Для персистентности добавьте базу данных (SQLite/PostgreSQL) в `context_manager.py`.

## 📄 Лицензия

MIT

## 🔗 Ссылки

- [aiogram документация](https://docs.aiogram.dev/)
- [ProxyApi.ru](https://proxyapi.ru)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
- [@BotFather](https://t.me/BotFather)
