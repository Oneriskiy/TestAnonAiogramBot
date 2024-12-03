
from config import Token
from aiogram import types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from text import StartText, HelpText, InfoText
from handlers import conversations,  searching_for_female, searching_for_male,is_user_in_conversation, UserState

bot = Bot(Token)
callbackrouter = Router()

@callbackrouter.callback_query(lambda c: c.data == 'help')
async def help_main(callback_query: types.CallbackQuery):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")],
        ])
    await callback_query.message.edit_text(HelpText,parse_mode="HTML", reply_markup=builder)


@callbackrouter.callback_query(lambda c: c.data == 'info')
async def info_main(callback_query: types.CallbackQuery):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")],
    ])
    await callback_query.message.edit_text(InfoText,parse_mode="HTML", reply_markup=builder)


@callbackrouter.callback_query(lambda c: c.data == 'register')
async def register_user(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите ваше имя:")
    await state.set_state(UserState.waiting_for_name)


@callbackrouter.callback_query(lambda c: c.data == 'BackToStart')
async def back_to_start(callback_query: types.CallbackQuery):
    builder = InlineKeyboardMarkup(inline_keyboard=[    
    [InlineKeyboardButton(text="Зарегистрироваться заново", callback_data="register")],
    [InlineKeyboardButton(text="Поиск пользователей", callback_data="search")],
    [InlineKeyboardButton(text="Информация о боте", callback_data="info")],
    [InlineKeyboardButton(text="Помощь", callback_data="help")]
])
    await callback_query.message.edit_text(StartText,parse_mode="HTML", reply_markup=builder)


@callbackrouter.callback_query(lambda c: c.data == 'search')
async def search_gender(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id


    if await is_user_in_conversation(user_id):
        await callback_query.answer("Вы не можете искать собеседников, пока не завершите текущий разговор.")
        return

 
    builder = InlineKeyboardMarkup(inline_keyboard=[    
        [InlineKeyboardButton(text="Мужчина", callback_data="search_male")],
        [InlineKeyboardButton(text="Женщина", callback_data="search_female")],
        [InlineKeyboardButton(text="Назад", callback_data="BackToStart")]
    ])
    
    await callback_query.message.edit_text("Выберите пол для поиска собеседника:", reply_markup=builder)


@callbackrouter.callback_query(lambda c: c.data == 'search_male')
async def search_male(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in conversations:
        await callback_query.answer("Вы уже ищете собеседника.")
        return

    if searching_for_male:
        partner_id = searching_for_male.pop(0)
        conversations[user_id] = partner_id
        conversations[partner_id] = user_id

        # Отправляем сообщения о подключении
        await bot.send_message(user_id, "Вы подключены к собеседнику!")
        await bot.send_message(partner_id, "Вы подключены к собеседнику!")

        # Убираем кнопку поиска
        builder = InlineKeyboardMarkup(inline_keyboard=[    
            [InlineKeyboardButton(text="Завершить разговор", callback_data="end_conversation")]
        ])
        await callback_query.message.edit_text("Вы в разговоре. Для завершения нажмите кнопку ниже.", reply_markup=builder)
    else:
        # Добавляем в очередь поиска
        searching_for_male.append(user_id)
        await callback_query.message.edit_text("Ожидайте подключения к собеседнику...")

# Хэндлер для поиска пользователей по полу (женщина)
@callbackrouter.callback_query(lambda c: c.data == 'search_female')
async def search_female(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Добавляем пользователя в очередь поиска женщин
    if user_id in conversations:
        await callback_query.answer("Вы уже ищете собеседника.")
        return

    # Пробуем найти собеседника для этого пользователя
    if searching_for_female:
        partner_id = searching_for_female.pop(0)
        conversations[user_id] = partner_id
        conversations[partner_id] = user_id

        # Отправляем сообщения о подключении
        await bot.send_message(user_id, "Вы подключены к собеседнику!")
        await bot.send_message(partner_id, "Вы подключены к собеседнику!")

        # Убираем кнопку поиска
        builder = InlineKeyboardMarkup(inline_keyboard=[    
            [InlineKeyboardButton(text="Завершить разговор", callback_data="end_conversation")]
        ])
        await callback_query.message.edit_text("Вы в разговоре. Для завершения нажмите кнопку ниже.", reply_markup=builder)
    else:
        # Добавляем в очередь поиска
        searching_for_female.append(user_id)
        await callback_query.message.edit_text("Ожидайте подключения к собеседнику...")

# Хэндлер для завершения разговора
@callbackrouter.callback_query(lambda c: c.data == 'stop')
async def end_conversation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await is_user_in_conversation(user_id):
        partner_id = conversations.pop(user_id)
        conversations.pop(partner_id, None)

        # Сообщаем собеседникам о завершении разговора
        await bot.send_message(user_id, "Вы завершили разговор.")
        await bot.send_message(partner_id, "Ваш собеседник завершил разговор.")

        # Возвращаем пользователя в главное меню
        builder = InlineKeyboardMarkup(inline_keyboard=[    
            [InlineKeyboardButton(text="Зарегистрироваться заново", callback_data="register")],
            [InlineKeyboardButton(text="Поиск пользователей", callback_data="search")],
            [InlineKeyboardButton(text="Информация о боте", callback_data="info")],
            [InlineKeyboardButton(text="Помощь", callback_data="help")]
        ])
        await callback_query.message.edit_text(StartText,parse_mode="HTML", reply_markup=builder)
    else:
        await callback_query.answer("Вы не находитесь в разговоре.")
