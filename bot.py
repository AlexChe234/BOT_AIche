"""
Telegram-бот с AI-ассистентом на базе ProxyApi.ru.
Поддержка контекста диалога и команды /reset.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BotCommand

from config import config, logger, error_logger
from context_manager import context_manager
from api_client import api_client, AIResponse

# =============================================================================
# Инициализация бота
# =============================================================================

if not config.validate():
    raise RuntimeError("Конфигурация не пройдена. Проверьте .env файл.")

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

logger.info("Бот инициализирован")


# =============================================================================
# Клавиатуры
# =============================================================================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создать основную клавиатуру с командами."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚀 Начать диалог"),
                KeyboardButton(text="🧹 Очистить историю")
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="❓ Справка")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


# =============================================================================
# Хелперы
# =============================================================================

async def send_typing_action(chat_id: int) -> None:
    """Отправить действие 'печатает'."""
    await bot.send_chat_action(chat_id=chat_id, action="typing")


def format_response(response: AIResponse, show_thinking: bool = False) -> str:
    """Форматировать ответ для отправки пользователю."""
    text = response.content
    
    # Добавляем информацию о токенах (для отладки можно раскомментировать)
    # if response.input_tokens and response.output_tokens:
    #     text += f"\n\n_Токены: {response.input_tokens} in / {response.output_tokens} out_"
    
    return text


# =============================================================================
# Обработчики команд
# =============================================================================

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} ({user_id}) запустил бота")
    
    # Получаем или создаём контекст
    context_manager.get_context(user_id)
    
    await message.answer(
        f"👋 Привет, {username}!\n\n"
        f"Я AI-ассистент. Задавай мне любые вопросы — я запомню контекст нашего диалога.\n\n"
        f"Используй кнопки внизу или команды:\n"
        f"• Очистить историю\n"
        f"• Статистика\n"
        f"• Справка\n\n"
        f"Просто напиши сообщение, и я отвечу!",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Обработчик команды /reset — очистка контекста."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    context_manager.clear_context(user_id)
    logger.info(f"Пользователь {username} ({user_id}) очистил контекст")
    
    await message.answer(
        "🧹 Контекст очищен!\n\n"
        "История переписки удалена. Начнём диалог заново.",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Обработчик команды /stats — статистика."""
    user_id = message.from_user.id
    context = context_manager.get_context(user_id)
    stats = context_manager.get_stats()
    
    await message.answer(
        f"📊 Статистика\n\n"
        f"Ваши сообщения в контексте: {context.message_count}\n"
        f"Активных пользователей: {stats['active_users']}\n"
        f"Всего сообщений в памяти: {stats['total_messages']}\n"
        f"Модель: {config.MODEL}",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help — справка."""
    await message.answer(
        "📖 Справка\n\n"
        "Я AI-ассистент, работающий через ProxyApi.ru.\n\n"
        "Команды:\n"
        "• /start — начать диалог\n"
        "• /reset — очистить историю переписки\n"
        "• /stats — показать статистику\n"
        "• /help — эта справка\n\n"
        "Как использовать:\n"
        "Просто напишите сообщение в чат, и я отвечу.\n"
        "Я запоминаю контекст диалога, поэтому можно задавать уточняющие вопросы.\n\n"
        f"Модель: {config.MODEL}",
        reply_markup=get_main_keyboard()
    )


# =============================================================================
# Обработчик кнопок меню
# =============================================================================

@dp.message(lambda msg: msg.text == "🚀 Начать диалог")
async def btn_start(message: Message) -> None:
    """Обработчик кнопки 'Начать диалог'."""
    await cmd_start(message)


@dp.message(lambda msg: msg.text == "🧹 Очистить историю")
async def btn_reset(message: Message) -> None:
    """Обработчик кнопки 'Очистить историю'."""
    await cmd_reset(message)


@dp.message(lambda msg: msg.text == "📊 Статистика")
async def btn_stats(message: Message) -> None:
    """Обработчик кнопки 'Статистика'."""
    await cmd_stats(message)


@dp.message(lambda msg: msg.text == "❓ Справка")
async def btn_help(message: Message) -> None:
    """Обработчик кнопки 'Справка'."""
    await cmd_help(message)


# =============================================================================
# Обработчик сообщений
# =============================================================================

@dp.message()
async def handle_message(message: Message) -> None:
    """Обработчик обычных сообщений."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_text = message.text
    
    if not user_text:
        return
    
    # Игнорируем сообщения, которые являются текстом кнопок
    button_texts = ["🚀 Начать диалог", "🧹 Очистить историю", "📊 Статистика", "❓ Справка"]
    if user_text in button_texts:
        return
    
    logger.info(f"Сообщение от {username} ({user_id}): {user_text[:50]}...")
    
    # Показываем действие "печатает"
    await send_typing_action(message.chat.id)
    
    # Получаем контекст и добавляем сообщение пользователя
    context = context_manager.get_context(user_id)
    context.add_message("user", user_text)
    
    try:
        # Отправляем запрос к API
        messages = context.get_messages()
        response = api_client.send_message(messages)
        
        # Добавляем ответ ассистента в контекст
        context.add_message("assistant", response.content)
        
        # Форматируем и отправляем ответ
        answer_text = format_response(response)
        
        await message.answer(
            answer_text,
            reply_markup=get_main_keyboard()
        )
        
        logger.info(f"Ответ отправлен пользователю {username} ({user_id})")
        
    except TimeoutError as e:
        error_logger.error(f"Таймаут для пользователя {user_id}: {e}")
        await message.answer(
            "⏱️ Таймаут\n\n"
            "Сервер не ответил вовремя. Попробуйте ещё раз.",
            reply_markup=get_main_keyboard()
        )
        
    except ConnectionError as e:
        error_logger.error(f"Ошибка соединения для пользователя {user_id}: {e}")
        await message.answer(
            "🔌 Ошибка соединения\n\n"
            "Не удалось подключиться к серверу. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        
    except RuntimeError as e:
        error_logger.error(f"Ошибка выполнения для пользователя {user_id}: {e}")
        await message.answer(
            f"❌ Ошибка\n\n{str(e)}",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        error_logger.exception(f"Неожиданная ошибка для пользователя {user_id}: {e}")
        await message.answer(
            "❌ Неожиданная ошибка\n\n"
            "Произошла ошибка при обработке запроса. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )


# =============================================================================
# Запуск бота
# =============================================================================

async def set_bot_commands() -> None:
    """Установить команды бота в меню."""
    commands = [
        BotCommand(command="start", description="🚀 Начать диалог"),
        BotCommand(command="reset", description="🧹 Очистить историю"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="help", description="❓ Справка")
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Команды бота установлены")


async def main() -> None:
    """Запуск бота."""
    logger.info("Запуск бота...")
    
    # Устанавливаем команды в меню
    await set_bot_commands()
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        error_logger.exception(f"Критическая ошибка при запуске: {e}")
        raise
