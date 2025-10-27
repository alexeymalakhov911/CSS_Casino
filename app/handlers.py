from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
import app.keyboards as kb
from better_profanity import profanity
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
import random
from app.blackjack import start_blackjack, choose_bet, hit, stand
from app.roulette import start_roulette_game, spin_roulette, RouletteStates
from app.currency import get_rate
router = Router()

class Register(StatesGroup):
    name = State()
    age = State()
    passport = State()
    number = State()

class Balance(StatesGroup):
    amount = State()

class ExitCasino(StatesGroup):
    roulette = State()

class Blackjack(StatesGroup):
    set_bet = State()
    playing = State()

class CurrencyStates(StatesGroup):
    waiting_for_pair = State()


user_balances = {}


@router.message(CommandStart())
async def cd_start(message: Message):
    await message.answer('Приветствуем в нашем казино!\n'
                         'Прочитайте наши правила, и зарегистрируйтесь, если согласны.', reply_markup=kb.start)

@router.callback_query(F.data == "info")
async def show_rules(callback: CallbackQuery):
    rules_text = (
        "📜 Правила казино:\n"
        "1. Минимальная ставка 100 монет.\n"
        "2. Выйти из казино можно только если Вы увеличили ваш баланс (Сумму пополнений) в 3 раза,"
        " либо сыграв в Русскую рулетку.\n"
        "3. Не используйте нецензурные слова. Первое использование - Предупреждение, Второе - Расстрел.\n"
        "4. Ваши персональные данные будут переданы 3 лицам, на вас будут взяты микрокредиты.\n"
        "Удачи!"

    )
    await callback.message.edit_text(rules_text, reply_markup=kb.rules_keyboard)

@router.callback_query(F.data == 'games')
async def return_to_menu(callback: CallbackQuery):
    await callback.message.answer('Главное меню', reply_markup=kb.games)


#Регистрация

@router.callback_query(F.data == 'register')
async def register(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Register.name)
    await callback.message.answer("Введите ваше имя:")

@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    if profanity.contains_profanity(message.text):
        await message.reply("Имя содержит запрещённые слова. Попробуйте снова.")
        return
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer("Введите ваш возраст:")

@router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Введите возраст цифрами, например: 25")
        return
    age = int(message.text)
    if age < 18:
        await message.reply("Вам должно быть 18 лет или больше для регистрации.")
        await state.clear()
        return

    await state.update_data(age=age)
    await state.set_state(Register.passport)
    await message.answer("Введите данные паспорта в формате xxxx xxxxxx:")

@router.message(Register.passport)
async def register_passport(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "")
    if not (text.isdigit() and len(text) == 10):
        await message.reply("Неверный формат паспорта. Пример: '1234 567890'")
        return

    await state.update_data(passport=message.text)
    await state.set_state(Register.number)
    await message.answer("Отправьте ваш номер телефона", reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Спасибо за регистрацию!\nВaшe имя: {data["name"]}\nВаш возраст: '
                         f'{data["age"]}\nПаспорт:{data["passport"]}\nНомер:{data["number"]}',
                         reply_markup=kb.after_register)
    await state.clear()

#Работа с балансом

@router.callback_query(F.data == 'replenishment')
async def replenishment_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Balance.amount)
    await callback.message.answer('💰Введите сумму пополнения кратную 100 💰')


@router.message(Balance.amount)
async def process_replenishment(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Введите только число, например 100, 500 или 1000")
        return

    amount = int(message.text)
    if amount % 100 != 0:
        await message.reply("Сумма должна быть кратна 100")
        return

    user_id = message.from_user.id

    if user_id not in user_balances:
        user_balances[user_id] = {"current_balance": 0, "total_replenished": 0}

    user_balances[user_id]["current_balance"] += amount
    user_balances[user_id]["total_replenished"] += amount

    balance = user_balances[user_id]["current_balance"]
    total = user_balances[user_id]["total_replenished"]

    await message.answer(f"🎉 Баланс успешно пополнен!\n"
                         f"Текущий баланс: {balance} монет\n"
                         f"Всего пополнено: {total} монет", reply_markup=kb.games)
    await state.clear()

@router.callback_query(F.data == 'balance')
async def balance_request(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = user_balances[user_id]["current_balance"]
    total = user_balances[user_id]["total_replenished"]
    await callback.message.answer(f"Текущий баланс: {balance} монет\n"
                                    f"Всего пополнено: {total} монет", reply_markup=kb.after_register)

#Выход

@router.callback_query(F.data == 'exit')
async def exit_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = user_balances.get(user_id, {}).get("current_balance", 0)
    total = user_balances.get(user_id, {}).get("total_replenished", 1)

    if balance / total < 3:
        await state.set_state(ExitCasino.roulette)
        await callback.message.answer(
            'Вы увеличили баланс меньше чем в 3 раза, вам нужно сыграть в русскую рулетку, чтобы уйти',
            reply_markup=kb.roulette
        )
    else:
        await callback.message.answer('✅ Вы можете выйти из казино. Спасибо за игру!')
        await state.clear()

@router.callback_query(F.data == 'shot', StateFilter(ExitCasino.roulette))
async def roulette_shot(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bullet = random.randint(1, 6)
    if bullet == 1:
        await callback.message.answer('💥 Бах! Вы убили себя!', reply_markup=kb.start)
        user_balances[user_id]["current_balance"] = 0
    else:
        await callback.message.answer('Вы смогли выйти из казино. До встречи)))')
    await state.clear()

@router.callback_query(F.data == 'stopexit', StateFilter(ExitCasino.roulette))
async def roulette_stopexit(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Вы решили остаться в казино.', reply_markup=kb.games)
    await state.clear()



#БлэкДжек
class BlackjackStates(StatesGroup):
    set_bet = State()
    player_turn = State()

@router.callback_query(F.data == "blackjack")
async def cb_start_blackjack(callback: CallbackQuery, state: FSMContext):
    await start_blackjack(callback, state, user_balances)

@router.callback_query(F.data.startswith("bet_"))
async def cb_choose_bet(callback: CallbackQuery, state: FSMContext):
    await choose_bet(callback, state, user_balances)

@router.callback_query(F.data == "hit")
async def cb_hit(callback: CallbackQuery, state: FSMContext):
    await hit(callback, state, user_balances)

@router.callback_query(F.data == "stand")
async def cb_stand(callback: CallbackQuery, state: FSMContext):
    await stand(callback, state, user_balances)

#Рулетка

@router.callback_query(F.data == "roulette")
async def cb_start_roulette(callback: CallbackQuery, state: FSMContext):
    await start_roulette_game(callback, state, user_balances)

@router.callback_query(
    F.data.startswith("rl_bet_"),
    StateFilter(RouletteStates.choosing_bet)
)
async def cb_spin_roulette(callback: CallbackQuery, state: FSMContext):
    await spin_roulette(callback, state, user_balances)

@router.callback_query(F.data == "roulette")
async def cb_play_again(callback: CallbackQuery, state: FSMContext):
    await start_roulette_game(callback, state, user_balances)

@router.callback_query(F.data == "menu")
async def cb_return_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Вы вернулись в главное меню.", reply_markup=kb.games)




#Курсы валют

@router.callback_query(F.data == "exchange")
async def cb_exchange(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CurrencyStates.waiting_for_pair)
    await callback.message.answer("Введите валютную пару, например: `rub usd` (через пробел)")


@router.message(CurrencyStates.waiting_for_pair)
async def get_currency_pair(message: Message, state: FSMContext):
    parts = message.text.strip().lower().split()

    if len(parts) != 2:
        await message.answer(
            "Формат неверный. Введите, например: `rub usd`",
            reply_markup=kb.currency_menu_kb)
        return

    code_1, code_2 = parts
    rate = get_rate(code_1, code_2)

    if isinstance(rate, dict) and "error" in rate:
        await message.answer(
            "Не удалось получить курс. Проверьте коды валют.",
            reply_markup=kb.currency_menu_kb)
    else:
        await message.answer(
            f"Курс:\n1 {code_1.upper()} = {rate} {code_2.upper()}",
            reply_markup=kb.currency_menu_kb)

    await state.clear()


#Бан за бранные слова

profanity.load_censor_words()
russian_badwords = ['попа','жопа' 'дерь' 'какашка', 'дурак', 'пиз',
                    'пид','eба', 'ху', 'сук', 'ебл', 'дау', 'бля'] #эта штука детектит большинство матерных слов
profanity.add_censor_words(russian_badwords)

@router.message()
async def check_profanity(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_balances:
        user_balances[user_id] = {"current_balance": 0, "total_replenished": 0, "profanity_count": 0}
    else:
        if "profanity_count" not in user_balances[user_id]:
            user_balances[user_id]["profanity_count"] = 0

    if profanity.contains_profanity(message.text):
        user_balances[user_id]["profanity_count"] += 1
        count = user_balances[user_id]["profanity_count"]

        if count == 1:
            await message.reply("Пожалуйста, не используйте нецензурные слова!"
                                " Это ваше первое и последнее предупреждение.")
        elif count >= 2:
            await message.reply("Расстрел.", reply_markup=kb.start)
            user_balances[user_id]["current_balance"] = 0
            user_balances[user_id]["profanity_count"] = 0
