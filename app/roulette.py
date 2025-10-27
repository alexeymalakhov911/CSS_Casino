import random
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class RouletteStates(StatesGroup):
    choosing_bet = State()

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

roulette_bet_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔴 Красное 🔴", callback_data="rl_bet_red"),
     InlineKeyboardButton(text="⚫ Чёрное ⚫", callback_data="rl_bet_black")],
    [InlineKeyboardButton(text="Чет", callback_data="rl_bet_even"),
     InlineKeyboardButton(text="Нечет", callback_data="rl_bet_odd")],
    [InlineKeyboardButton(text="🟢 Зеро 🟢", callback_data="rl_bet_zero")],
    [InlineKeyboardButton(text="В главное меню", callback_data="menu")]])

after_spin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сыграть снова", callback_data="roulette")],
    [InlineKeyboardButton(text="В главное меню", callback_data="menu")]])

async def start_roulette_game(callback: CallbackQuery, state: FSMContext, user_balances):
    user_id = callback.from_user.id
    if user_balances.get(user_id, {}).get("current_balance", 0) <= 0:
        from app.keyboards import games
        await callback.message.answer("Баланс пуст. Пополните баланс.", reply_markup=games.replenishment)
        return
    await state.set_state(RouletteStates.choosing_bet)
    await callback.message.answer("Ставка 100 монет.\nВыберите тип ставки:", reply_markup=roulette_bet_keyboard)

async def spin_roulette(callback: CallbackQuery, state: FSMContext, user_balances):
    user_id = callback.from_user.id
    balance = user_balances[user_id]["current_balance"]
    bet_amount = 100
    if bet_amount > balance:
        from app.keyboards import games
        await callback.message.answer("Недостаточно средств. Пополните баланс.", reply_markup=games.replenishment)
        await state.clear()
        return

    bet_type = callback.data.split("_")[2]
    spin_result = random.randint(0, 36)
    win = False
    payout = bet_amount

    if bet_type == "red" and spin_result in RED_NUMBERS:
        win = True
    elif bet_type == "black" and spin_result in BLACK_NUMBERS:
        win = True
    elif bet_type == "even" and spin_result != 0 and spin_result % 2 == 0:
        win = True
    elif bet_type == "odd" and spin_result % 2 == 1:
        win = True
    elif bet_type == "zero" and spin_result == 0:
        win = True
        payout *= 36

    if win:
        user_balances[user_id]["current_balance"] += payout
        result_text = f"Выпало {spin_result}. Вы выиграли {payout} монет!"
    else:
        user_balances[user_id]["current_balance"] -= bet_amount
        result_text = f"Выпало {spin_result}. Вы проиграли {bet_amount} монет."

    await callback.message.answer(
        f"{result_text}\nБаланс: {user_balances[user_id]['current_balance']} монет",
        reply_markup=after_spin_keyboard
    )
    await state.clear()

