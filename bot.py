"""
Telegram-бот с AI-ассистентом на базе ProxyApi.ru.
Поддержка контекста диалога, выбор температуры и моделей.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config, logger, error_logger
from context_manager import context_manager
from api_client import api_client, AIResponse


# =============================================================================
# Состояния (FSM)
# =============================================================================

class MenuState(StatesGroup):
    MAIN = State()          # Главное меню
    SETTINGS = State()      # Настройки
    TEMPERATURE = State()   # Выбор температуры
    MODEL_PROVIDER = State() # Выбор провайдера
    MODEL_OPENAI = State()  # Модели OpenAI
    MODEL_ANTHROPIC = State() # Модели Anthropic
    MODEL_GOOGLE = State()  # Модели Google

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
            ],
            [
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_settings_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру настроек."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌡️ Температура"),
                KeyboardButton(text="🤖 Выбрать модель")
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_temperature_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру выбора температуры (0.0 - 1.0 с шагом 0.1)."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="0.0"),
                KeyboardButton(text="0.1"),
                KeyboardButton(text="0.2")
            ],
            [
                KeyboardButton(text="0.3"),
                KeyboardButton(text="0.4"),
                KeyboardButton(text="0.5")
            ],
            [
                KeyboardButton(text="0.6"),
                KeyboardButton(text="0.7"),
                KeyboardButton(text="0.8")
            ],
            [
                KeyboardButton(text="0.9"),
                KeyboardButton(text="1.0")
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_model_providers_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру выбора провайдера моделей."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟦 OpenAI"),
                KeyboardButton(text="🟪 Anthropic")
            ],
            [
                KeyboardButton(text="🟥 Google")
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_openai_models_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру моделей OpenAI."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=model)] for model in config.OPENAI_MODELS
        ] + [[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_anthropic_models_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру моделей Anthropic."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=model)] for model in config.ANTHROPIC_MODELS
        ] + [[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_google_models_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру моделей Google."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=model)] for model in config.GOOGLE_MODELS
        ] + [[KeyboardButton(text="🔙 Назад")]],
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
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} ({user_id}) запустил бота")
    
    # Получаем или создаём контекст
    context_manager.get_context(user_id)
    
    # Сбрасываем состояние в главное меню
    await state.set_state(MenuState.MAIN)
    
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
async def cmd_reset(message: Message, state: FSMContext) -> None:
    """Обработчик команды /reset — очистка контекста."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    context_manager.clear_context(user_id)
    logger.info(f"Пользователь {username} ({user_id}) очистил контекст")
    
    await state.set_state(MenuState.MAIN)
    
    await message.answer(
        "🧹 Контекст очищен!\n\n"
        "История переписки удалена. Начнём диалог заново.",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext) -> None:
    """Обработчик команды /stats — статистика."""
    user_id = message.from_user.id
    context = context_manager.get_context(user_id)
    stats = context_manager.get_stats()
    
    await state.set_state(MenuState.MAIN)
    
    await message.answer(
        f"📊 Статистика\n\n"
        f"Ваши сообщения в контексте: {context.message_count}\n"
        f"Активных пользователей: {stats['active_users']}\n"
        f"Всего сообщений в памяти: {stats['total_messages']}\n"
        f"Модель: {context.model}\n"
        f"Температура: {context.temperature}",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    """Обработчик команды /help — справка."""
    await state.set_state(MenuState.MAIN)
    
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
        "Настройки:\n"
        "• Температура — креативность ответов (0.0 - 1.0)\n"
        "• Модель — выбор AI модели (OpenAI, Anthropic, Google)",
        reply_markup=get_main_keyboard()
    )


# =============================================================================
# Обработчик кнопок меню
# =============================================================================

@dp.message(lambda msg: msg.text == "🚀 Начать диалог")
async def btn_start(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Начать диалог'."""
    await state.set_state(MenuState.MAIN)
    await cmd_start(message, state)


@dp.message(lambda msg: msg.text == "🧹 Очистить историю")
async def btn_reset(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Очистить историю'."""
    await state.set_state(MenuState.MAIN)
    await cmd_reset(message, state)


@dp.message(lambda msg: msg.text == "📊 Статистика")
async def btn_stats(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Статистика'."""
    await state.set_state(MenuState.MAIN)
    await cmd_stats(message, state)


@dp.message(lambda msg: msg.text == "❓ Справка")
async def btn_help(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Справка'."""
    await state.set_state(MenuState.MAIN)
    await cmd_help(message, state)


@dp.message(lambda msg: msg.text == "⚙️ Настройки")
async def btn_settings(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Настройки'."""
    user_id = message.from_user.id
    context = context_manager.get_context(user_id)
    
    await state.set_state(MenuState.SETTINGS)
    
    await message.answer(
        f"⚙️ Настройки\n\n"
        f"Текущая модель: {context.model}\n"
        f"Текущая температура: {context.temperature}\n\n"
        f"Выберите параметр для изменения:",
        reply_markup=get_settings_keyboard()
    )


@dp.message(lambda msg: msg.text == "🌡️ Температура")
async def btn_temperature(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Температура'."""
    user_id = message.from_user.id
    context = context_manager.get_context(user_id)
    
    await state.set_state(MenuState.TEMPERATURE)
    
    await message.answer(
        f"🌡️ Выбор температуры\n\n"
        f"Текущее значение: {context.temperature}\n\n"
        f"Температура влияет на креативность ответов:\n"
        f"• 0.0 — максимально точные и детерминированные\n"
        f"• 0.7 — сбалансированные (по умолчанию)\n"
        f"• 1.0 — максимально креативные\n\n"
        f"Выберите значение:",
        reply_markup=get_temperature_keyboard()
    )


@dp.message(lambda msg: msg.text == "🤖 Выбрать модель")
async def btn_select_model(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Выбрать модель'."""
    await state.set_state(MenuState.MODEL_PROVIDER)
    
    await message.answer(
        "🤖 Выбор провайдера\n\n"
        "Выберите провайдера моделей:",
        reply_markup=get_model_providers_keyboard()
    )


@dp.message(lambda msg: msg.text == "🟦 OpenAI")
async def btn_openai_models(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'OpenAI'."""
    await state.set_state(MenuState.MODEL_OPENAI)
    
    await message.answer(
        "🟦 Модели OpenAI\n\n"
        "Выберите модель:",
        reply_markup=get_openai_models_keyboard()
    )


@dp.message(lambda msg: msg.text == "🟪 Anthropic")
async def btn_anthropic_models(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Anthropic'."""
    await state.set_state(MenuState.MODEL_ANTHROPIC)
    
    await message.answer(
        "🟪 Модели Anthropic\n\n"
        "Выберите модель:",
        reply_markup=get_anthropic_models_keyboard()
    )


@dp.message(lambda msg: msg.text == "🟥 Google")
async def btn_google_models(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Google'."""
    await state.set_state(MenuState.MODEL_GOOGLE)
    
    await message.answer(
        "🟥 Модели Google\n\n"
        "Выберите модель:",
        reply_markup=get_google_models_keyboard()
    )


@dp.message(lambda msg: msg.text == "🔙 Назад")
async def btn_back(message: Message, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад'."""
    current_state = await state.get_state()
    user_id = message.from_user.id
    context = context_manager.get_context(user_id)
    
    # Навигация по уровням
    if current_state == MenuState.SETTINGS:
        # Из настроек → в главное меню
        await state.set_state(MenuState.MAIN)
        await message.answer(
            "🔙 Главное меню",
            reply_markup=get_main_keyboard()
        )
    elif current_state in [MenuState.TEMPERATURE, MenuState.MODEL_PROVIDER]:
        # Из температуры или выбора провайдера → в настройки
        await state.set_state(MenuState.SETTINGS)
        await message.answer(
            f"⚙️ Настройки\n\n"
            f"Текущая модель: {context.model}\n"
            f"Текущая температура: {context.temperature}\n\n"
            f"Выберите параметр для изменения:",
            reply_markup=get_settings_keyboard()
        )
    elif current_state in [MenuState.MODEL_OPENAI, MenuState.MODEL_ANTHROPIC, MenuState.MODEL_GOOGLE]:
        # Из выбора модели → к выбору провайдера
        await state.set_state(MenuState.MODEL_PROVIDER)
        await message.answer(
            "🤖 Выбор провайдера\n\n"
            "Выберите провайдера моделей:",
            reply_markup=get_model_providers_keyboard()
        )
    else:
        # По умолчанию → в настройки
        await state.set_state(MenuState.SETTINGS)
        await message.answer(
            f"⚙️ Настройки\n\n"
            f"Текущая модель: {context.model}\n"
            f"Текущая температура: {context.temperature}\n\n"
            f"Выберите параметр для изменения:",
            reply_markup=get_settings_keyboard()
        )
        

# Обработчики выбора температуры
TEMP_VALUES = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]

@dp.message(lambda msg: msg.text in TEMP_VALUES)
async def btn_set_temperature(message: Message, state: FSMContext) -> None:
    """Обработчик выбора температуры."""
    user_id = message.from_user.id
    temp = float(message.text)
    context = context_manager.get_context(user_id)
    context.set_temperature(temp)
    
    await state.set_state(MenuState.SETTINGS)
    
    await message.answer(
        f"✅ Температура установлена: {temp}\n\n"
        f"Текущая модель: {context.model}",
        reply_markup=get_settings_keyboard()
    )


# Обработчики выбора моделей
ALL_MODELS = config.OPENAI_MODELS + config.ANTHROPIC_MODELS + config.GOOGLE_MODELS

@dp.message(lambda msg: msg.text in ALL_MODELS)
async def btn_set_model(message: Message, state: FSMContext) -> None:
    """Обработчик выбора модели."""
    user_id = message.from_user.id
    model = message.text
    context = context_manager.get_context(user_id)
    context.set_model(model)
    
    # Определяем провайдера
    if model in config.OPENAI_MODELS:
        provider = "🟦 OpenAI"
    elif model in config.ANTHROPIC_MODELS:
        provider = "🟪 Anthropic"
    else:
        provider = "🟥 Google"
    
    # Возвращаем в главное меню после выбора модели
    await state.set_state(MenuState.MAIN)
    
    await message.answer(
        f"✅ Модель установлена: {model}\n"
        f"Провайдер: {provider}\n"
        f"Температура: {context.temperature}\n\n"
        f"Теперь вы можете начать диалог!",
        reply_markup=get_main_keyboard()
    )


# =============================================================================
# Обработчик сообщений
# =============================================================================

@dp.message(lambda msg: msg.text and not msg.text.startswith("/"))
async def handle_message(message: Message, state: FSMContext) -> None:
    """Обработчик обычных сообщений."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_text = message.text
    
    if not user_text:
        return
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    # Если пользователь в меню настроек - игнорируем текстовые сообщения
    if current_state != MenuState.MAIN:
        return
    
    # Игнорируем сообщения, которые являются текстом кнопок
    button_texts = [
        "🚀 Начать диалог", "🧹 Очистить историю", "📊 Статистика", "❓ Справка",
        "⚙️ Настройки", "🌡️ Температура", "🤖 Выбрать модель", "🔙 Назад",
        "🟦 OpenAI", "🟪 Anthropic", "🟥 Google",
        *TEMP_VALUES, *ALL_MODELS
    ]
    if user_text in button_texts:
        return
    
    logger.info(f"Сообщение от {username} ({user_id}): {user_text[:50]}...")
    
    # Показываем действие "печатает"
    await send_typing_action(message.chat.id)
    
    # Получаем контекст и добавляем сообщение пользователя
    context = context_manager.get_context(user_id)
    context.add_message("user", user_text)
    
    try:
        # Обновляем модель в клиенте, если она изменилась
        if api_client.model != context.model:
            api_client.set_model(context.model)
        
        # Отправляем запрос к API с температурой пользователя
        messages = context.get_messages()
        response = api_client.send_message(messages, temperature=context.temperature)
        
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
