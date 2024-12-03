import logging
from config import Token
from aiogram import types, Router, Dispatcher, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from users import add_or_update_user, get_user_profile
from text import StartText, HelpText, InfoText

dp = Dispatcher()
router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(Token)

# Инициализация словаря для отслеживания разговоров и поиска собеседников
conversations = {}
searching_for_male = []  # Список пользователей, которые ищут мужчину
searching_for_female = []  # Список пользователей, которые ищут женщину

# Определение состояний
class UserState(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_interests = State()
    browsing_profiles = State()

# Функция проверки, участвует ли пользователь в разговоре
async def is_user_in_conversation(user_id):
    """Проверка, участвует ли пользователь в разговоре."""
    return user_id in conversations and conversations[user_id] is not None

# Хэндлер /start
@router.message(CommandStart())
async def start_command(message: types.Message):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
    [InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")],
    [InlineKeyboardButton(text="Поиск пользователей", callback_data="search")],
    [InlineKeyboardButton(text="Информация о боте", callback_data="info")],
    [InlineKeyboardButton(text="Помощь", callback_data="help")]
])

    await message.answer(StartText,parse_mode="HTML", reply_markup=builder)

@router.message(Command('stop'))
async def stop_conversation(message: types.Message):
    user_id = message.from_user.id
    partner_id = await stop(user_id)  # Завершаем разговор для пользователя
    
    if partner_id:
        # Сообщаем собеседнику о завершении разговора
        await bot.send_message(partner_id, "Ваш собеседник завершил разговор.")
        await message.answer("Вы завершили разговор. Спасибо за общение!")
    else:
        await message.answer("Вы не подключены к собеседнику, чтобы завершить разговор.")

# Хэндлер /help
@router.message(Command('help'))
async def help_command(message: types.Message):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")],
])
    await message.answer(HelpText,parse_mode="HTML", reply_markup=builder)


# Хэндлер /info
@router.message(Command('info'))
async def info_command(message: types.Message):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")],
    ])
    await message.answer(InfoText,parse_mode="HTML", reply_markup=builder)

@router.message(Command('send'))
async def send_profile(message: types.Message):
    user_id = message.from_user.id
    if user_id in conversations and conversations[user_id] is not None:
        partner_id = conversations[user_id]

        # Получаем профиль пользователя из базы данных
        user_data = await get_user_profile(user_id)

        if user_data:
            # Формируем анкету
            profile = (
                f"Имя: {user_data['name']}\n"
                f"Возраст: {user_data['age']}\n"
                f"Пол: {user_data['gender']}\n"
                f"Интересы: {user_data['interests']}"
            )

            # Отправляем анкету собеседнику
            await bot.send_message(partner_id, f"Вот анкета пользователя :\n\n{profile}")
            await message.answer("Ваша анкета была отправлена собеседнику.")
        else:
            await message.answer("У вас нет анкеты. Пожалуйста, создайте её сначала, используя /register.")
    else:
        await message.answer("Вы не подключены к собеседнику. Для начала общения используйте команду /connect.")

@router.message(Command('connect'))
async def connect_command(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, не участвует ли пользователь уже в разговоре
    if await is_user_in_conversation(user_id):
        await message.answer("Вы уже подключены к собеседнику.")
        return

    # Проверяем, не находится ли пользователь в процессе поиска
    if user_id in searching_for_male or user_id in searching_for_female:
        await message.answer("Вы уже в процессе поиска собеседника. Пожалуйста, подождите.")
        return

    # Отправляем выбор пола для поиска собеседника
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Мужчина", callback_data="search_male")],
        [InlineKeyboardButton(text="Женщина", callback_data="search_female")],
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")]
    ])
    await message.answer("Выберите пол для поиска собеседника:", reply_markup=builder)


@router.message(Command('profile'))
async def profile_command(message: types.Message):
    user_id = message.from_user.id

    # Получаем профиль пользователя из базы данных
    user_data = await get_user_profile(user_id)

    if user_data:
        # Формируем и отправляем анкету
        profile = (
            f"Имя: {user_data['name']}\n"
            f"Возраст: {user_data['age']}\n"
            f"Пол: {user_data['gender']}\n"
            f"Интересы: {user_data['interests']}"
        )
        await message.answer(f"Ваш профиль:\n\n{profile}")
    else:
        await message.answer("У вас нет анкеты. Пожалуйста, создайте её сначала, используя команду /register.")

# Хэндлер для имени
@router.message(StateFilter(UserState.waiting_for_name))
async def set_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.answer("Введите ваш возраст:")
    await state.set_state(UserState.waiting_for_age)

# Хэндлер для возраста
@router.message(StateFilter(UserState.waiting_for_age))
async def set_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.answer("Введите ваш пол (мужчина/женщина):")
        await state.set_state(UserState.waiting_for_gender)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст.")

# Хэндлер для пола
@router.message(StateFilter(UserState.waiting_for_gender))
async def set_gender(message: types.Message, state: FSMContext):
    gender = message.text.lower()
    if gender not in ['мужчина', 'женщина']:
        await message.answer("Пожалуйста, введите 'мужчина' или 'женщина'.")
        return
    await state.update_data(gender=gender)
    await message.answer("Введите ваши интересы (через запятую):")
    await state.set_state(UserState.waiting_for_interests)

# Хэндлер для интересов
@router.message(StateFilter(UserState.waiting_for_interests))
async def set_interests(message: types.Message, state: FSMContext):
    interests = message.text
    await state.update_data(interests=interests)

    # Сохраняем данные в базе данных
    user_data = await state.get_data()
    await add_or_update_user(message.from_user.id, user_data['name'], user_data['age'], user_data['gender'], user_data['interests'])
    await message.answer("Ваш профиль создан! Вы можете искать других пользователей или редактировать свой профиль")
    await state.clear()

# Хэндлер для получения сообщений от пользователей
@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in conversations:
        partner_id = conversations[user_id]
        
        if partner_id:
            # Пересылаем сообщение второму пользователю
            await bot.send_message(partner_id, f"{message.text}")
        else:
            # Если собеседника нет, информируем пользователя
            await message.answer("Вы пока не подключены к собеседнику. Нажмите /connect для начала общения.")
    else:
        # Если пользователь не подключен к боту
        await message.answer("Введите команду /start для начала общения.")

# Функция для завершения диалога
async def stop(user_id):
    if user_id in conversations:
        partner_id = conversations[user_id]
        conversations.pop(user_id, None)
        conversations.pop(partner_id, None)
        return partner_id
    return None


# Кнопка завершения диалога в клавиатуре
@router.message()
async def send_message_with_end_button(message: types.Message):
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить диалог", callback_data="stop")]
    ])
    
    await message.answer("Нажмите кнопку ниже, чтобы завершить диалог", reply_markup=builder)
