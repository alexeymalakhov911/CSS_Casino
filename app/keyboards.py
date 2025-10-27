from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


start = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Регистрация', callback_data='register')],
                                              [InlineKeyboardButton(text='Правила', callback_data='info')]])

rules_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="C правилами согласен", callback_data="register")]])

games = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🃏 Блэкджек', callback_data='blackjack')],
    [InlineKeyboardButton(text='🎰 Рулетка', callback_data='roulette')],
    [InlineKeyboardButton(text='💱 Курсы валют', callback_data='exchange')],
    [InlineKeyboardButton(text='💰 Баланс', callback_data='balance')],
    [InlineKeyboardButton(text='🚪 Выйти из казино', callback_data='exit')]])


get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер',request_contact=True)]],
                                 resize_keyboard=True, one_time_keyboard=True)

after_register = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пополнить баланс',
                                                                             callback_data='replenishment')]])


roulette = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выстрелить", callback_data="shot")],
    [InlineKeyboardButton(text="Остаться", callback_data="stopexit")]])

currency_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔁 Ввести другую пару", callback_data="exchange")],
    [InlineKeyboardButton(text="🏠 В главное меню", callback_data="menu")]])