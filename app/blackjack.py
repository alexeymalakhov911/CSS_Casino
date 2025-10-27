import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

suits = ['♠', '♥', '♦', '♣']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def create_deck():
    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def calculate_hand_value(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            value += 11
            aces += 1
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def blackjack_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Взять карту", callback_data="hit"),
         InlineKeyboardButton(text="✋ Стоп", callback_data="stand")]
    ])

def bet_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="100", callback_data="bet_100"),
         InlineKeyboardButton(text="500", callback_data="bet_500"),
         InlineKeyboardButton(text="1000", callback_data="bet_1000")]
    ])

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games")],
        [InlineKeyboardButton(text="💳 Баланс", callback_data="balance")]
    ])

async def start_blackjack(callback, state, user_balances):
    user_id = callback.from_user.id
    if user_balances.get(user_id, {}).get("current_balance", 0) <= 0:
        await callback.message.answer(
            "У вас нулевой баланс. Пополните баланс, чтобы играть.",
            reply_markup=main_menu_keyboard()
        )
        return
    await state.set_state("set_bet")
    await callback.message.answer("Выберите ставку:", reply_markup=bet_keyboard())

async def choose_bet(callback, state, user_balances):
    user_id = callback.from_user.id
    bet_amount = int(callback.data.split("_")[1])
    if bet_amount > user_balances[user_id]["current_balance"]:
        await callback.message.answer(
            "Недостаточно средств. Пополните баланс.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return
    await state.update_data(bet=bet_amount)
    await callback.message.answer(f"Вы поставили {bet_amount} монет.")
    await state.set_state("player_turn")

    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    await state.update_data(deck=deck, player_hand=player_hand, dealer_hand=dealer_hand)
    await callback.message.answer(
        f"Ваши карты: {', '.join(player_hand)} (сумма: {calculate_hand_value(player_hand)})\n"
        f"Карта дилера: {dealer_hand[0]}, ?",
        reply_markup=blackjack_keyboard()
    )

async def hit(callback, state, user_balances):
    data = await state.get_data()
    deck = data["deck"]
    player_hand = data["player_hand"]
    dealer_hand = data["dealer_hand"]
    bet = data["bet"]
    user_id = callback.from_user.id

    player_hand.append(deck.pop())
    player_value = calculate_hand_value(player_hand)

    if player_value > 21:
        user_balances[user_id]["current_balance"] -= bet
        await callback.message.answer(
            f"Вы проиграли! Ваши карты: {', '.join(player_hand)} (сумма: {player_value})\n"
            f"Баланс: {user_balances[user_id]['current_balance']} монет",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    await state.update_data(player_hand=player_hand, deck=deck)
    await callback.message.edit_text(
        f"Ваши карты: {', '.join(player_hand)} (сумма: {player_value})\n"
        f"Карта дилера: {dealer_hand[0]}, ?",
        reply_markup=blackjack_keyboard()
    )

async def stand(callback, state, user_balances):
    data = await state.get_data()
    deck = data["deck"]
    player_hand = data["player_hand"]
    dealer_hand = data["dealer_hand"]
    bet = data["bet"]
    user_id = callback.from_user.id

    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand.append(deck.pop())

    player_value = calculate_hand_value(player_hand)
    dealer_value = calculate_hand_value(dealer_hand)

    if dealer_value > 21 or player_value > dealer_value:
        user_balances[user_id]["current_balance"] += bet
        result_text = "Вы выиграли!"
    elif player_value < dealer_value:
        user_balances[user_id]["current_balance"] -= bet
        result_text = "Вы проиграли!"
    else:
        result_text = "Ничья!"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    new_game_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Новая игра", callback_data="blackjack")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="games")]
    ])

    await callback.message.edit_text(
        f"Ваши карты: {', '.join(player_hand)} (сумма: {player_value})\n"
        f"Карты дилера: {', '.join(dealer_hand)} (сумма: {dealer_value})\n"
        f"{result_text}\nБаланс: {user_balances[user_id]['current_balance']} монет",
        reply_markup=new_game_keyboard
    )
    await state.clear()

