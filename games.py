import asyncio
import random
from aiogram import Router, F, types, Bot
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import get_display_name, escape_html
import database as db
import keyboards as kb
from shared import WIN_EMOJI, LOSE_EMOJI, edit_or_answer

router = Router()


@router.callback_query(F.data.startswith("blackjack:"))
async def blackjack_callback_handler(callback: types.CallbackQuery, game_id: str, move: str):
    game_data = db.get_blackjack_game(game_id)

    if not game_data:
        await callback.answer("This game has expired. Too slow!", show_alert=True)
        await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, callback.message.text, reply_markup=None, inline_message_id=callback.inline_message_id)
        return

    if callback.from_user.id != game_data['user_id']:
        return await callback.answer("This is not your game bro!", show_alert=True)

    if move == 'hit':
        await blackjack_hit_logic(callback, game_id, game_data)
    elif move == 'stand':
        await blackjack_stand_logic(callback, game_id, game_data)

router = Router()

# --- Slots --- 

async def start_slots(user: types.User, amount: int) -> str | None:
    is_cd, time_left, roast = db.get_cooldown_status(user.id, "slots", 7)
    if is_cd:
        return roast

    balance = db.get_user_balance(user.id)

    if amount <= 0:
        return "You can't bet zero or negative points, you absolute NPC."
    if balance < amount:
        return f"LMAO bro is broke 😭. You only have <b>{balance}</b> Rizz Points."

    db.lock_points(user.id, amount)
    db.update_cooldown(user.id, "slots")
    return None

@router.message(Command("slots"))
async def slots_handler(message: types.Message, command: CommandObject):
    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    if not command.args or not command.args.isdigit():
        await message.reply("Please specify a valid amount to play the slots!\nUsage: <code>/slots &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)
    error_message = await start_slots(user, amount)
    if error_message:
        await message.reply(error_message, parse_mode="HTML")
        return
    
    sent_message = await message.reply("Spinning the slots...")
    await process_slots(message.bot, user, amount, chat_id=sent_message.chat.id, message_id=sent_message.message_id)

async def process_slots(bot: Bot, user: types.User, amount: int, chat_id: int = None, message_id: int = None, inline_message_id: str = None):
    reels = ["🍒", "🍋", "💎", "💰", "⭐"]
    reel1 = random.choice(reels)
    reel2 = random.choice(reels)
    reel3 = random.choice(reels)

    slot_machine_msg = f"🎰 <b>[ {reel1} | {reel2} | {reel3} ]</b> 🎰"

    if reel1 == reel2 == reel3:
        if reel1 == "💎":
            payout = amount * 5
            win_msg = f"HOLY MOLY! TRIPLE DIAMONDS! Absolute W. You bagged <b>{payout}</b> RP! {random.choice(WIN_EMOJI)}"
        else:
            payout = amount * 2
            win_msg = f"JACKPOT! You won <b>{payout}</b> RP! Let him cook! {random.choice(WIN_EMOJI)}"
        
        db.update_user_balance(user.id, payout)
        new_balance = db.get_user_balance(user.id)
        
        text = f"{slot_machine_msg}\n\n{win_msg}\n\nYour new balance: <b>{new_balance}</b> RP."
    else:
        new_balance = db.get_user_balance(user.id)
        lose_msg = f"Unlucky fam. You got cooked and lost <b>{amount}</b> RP. {random.choice(LOSE_EMOJI)}"
        text = f"{slot_machine_msg}\n\n{lose_msg}\n\nYour new balance: <b>{new_balance}</b> RP."

    await edit_or_answer(bot, chat_id, message_id, text, reply_markup=kb.create_slots_keyboard(user.id, amount), inline_message_id=inline_message_id)

@router.callback_query(F.data.startswith("slots:play_again"))
async def slots_play_again_callback(callback: types.CallbackQuery):
    _, _, user_id_str, amount_str = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        return await callback.answer("This is not your machine bro!", show_alert=True)

    is_cd, time_left, roast = db.get_cooldown_status(user_id, "slots", 7)
    if is_cd:
        return await callback.answer(roast, show_alert=True)

    balance = db.get_user_balance(user_id)
    if balance < amount:
        await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, "Bro you don't even have enough Rizz Points to spin again. Negative aura.", inline_message_id=callback.inline_message_id)
        return await callback.answer("Not enough points.", show_alert=True)

    db.lock_points(user_id, amount)
    db.update_cooldown(user_id, "slots")
    
    await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, "Spinning the slots...", inline_message_id=callback.inline_message_id)
    await process_slots(callback.bot, callback.from_user, amount, chat_id=callback.message.chat.id if callback.message else None, message_id=callback.message.message_id if callback.message else None, inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("coinflip:guess:"))
async def coinflip_guess_callback(callback: types.CallbackQuery):
    _, _, user_id_str, amount_str, guess = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        return await callback.answer("This is not your coinflip bro. Play your own game!", show_alert=True)

    outcome = random.choice(["heads", "tails"])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Play Again 🪙", callback_data=f"coinflip:replay:{user_id}:{amount}")
    
    if guess == outcome:
        winnings = amount
        db.update_user_balance(user_id, winnings)
        new_balance = db.get_user_balance(user_id)
        
        text = (
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>!\n"
            f"You guessed correctly and secured <b>{amount}</b> RP in profit! {random.choice(WIN_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP."
        )
    else:
        new_balance = db.get_user_balance(user_id)
        
        text = (
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>.\n"
            f"You guessed wrong and got cooked for <b>{amount}</b> RP. {random.choice(LOSE_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP."
        )

    await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, text, reply_markup=builder.as_markup(), inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("coinflip:guess:"))
async def coinflip_guess_callback(callback: types.CallbackQuery):
    _, _, user_id_str, amount_str, guess = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        return await callback.answer("This is not your coinflip bro. Play your own game!", show_alert=True)

    outcome = random.choice(["heads", "tails"])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Play Again 🪙", callback_data=f"coinflip:replay:{user_id}:{amount}")
    
    if guess == outcome:
        winnings = amount
        db.update_user_balance(user_id, winnings)
        new_balance = db.get_user_balance(user_id)
        
        text = (
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>!\n"
            f"You guessed correctly and secured <b>{amount}</b> RP in profit! {random.choice(WIN_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP."
        )
    else:
        new_balance = db.get_user_balance(user_id)
        
        text = (
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>.\n"
            f"You guessed wrong and got cooked for <b>{amount}</b> RP. {random.choice(LOSE_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP."
        )

    await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, text, reply_markup=builder.as_markup(), inline_message_id=callback.inline_message_id)
    await callback.answer()

import json

# --- Blackjack ---

CARDS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

def get_card_value(card: str) -> int:
    return CARDS[card]

def calculate_hand_value(hand: list) -> int:
    value = sum(get_card_value(card) for card in hand)
    num_aces = hand.count('A')
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

def deal_card(deck: list) -> str:
    return deck.pop()

async def start_blackjack(user: types.User, amount: int, game_id: str) -> tuple[str | None, dict | None]:
    is_cd, time_left, roast = db.get_cooldown_status(user.id, "blackjack", 5)
    if is_cd:
        return roast, None

    balance = db.get_user_balance(user.id)

    if amount <= 0:
        return "You can't bet zero or negative points, you absolute NPC.", None
    if balance < amount:
        return f"Bro is literally broke 😭. You only have <b>{balance}</b> RP.", None

    db.lock_points(user.id, amount)
    deck = list(CARDS.keys()) * 4
    random.shuffle(deck)

    player_hand = [deal_card(deck), deal_card(deck)]
    dealer_hand = [deal_card(deck), deal_card(deck)]

    game_state = {
        "user_id": user.id,
        "amount": amount,
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "game_state": "player_turn"
    }
    
    db.create_blackjack_game(game_id, user.id, json.dumps(deck), json.dumps(player_hand), json.dumps(dealer_hand), amount, "player_turn")
    db.update_cooldown(user.id, "blackjack")
    return None, game_state

@router.message(Command("blackjack"))
async def blackjack_handler(message: types.Message, command: CommandObject):
    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    if not command.args or not command.args.isdigit():
        await message.reply("Please specify a valid amount to play blackjack!\nUsage: <code>/blackjack &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)
    game_id = f"blackjack_{message.chat.id}_{message.message_id}"
    error_message, game_state = await start_blackjack(user, amount, game_id)

    if error_message:
        await message.reply(error_message, parse_mode="HTML")
        return

    sent_message = await message.reply(
        f"Starting blackjack for <b>{amount}</b> RP... Let him cook! 🃏",
        parse_mode="HTML"
    )
    await show_blackjack_state(message.bot, game_id, chat_id=sent_message.chat.id, message_id=sent_message.message_id)

async def show_blackjack_state(bot: Bot, game_id: str, chat_id: int = None, message_id: int = None, inline_message_id: str = None, final: bool = False):
    game_data = db.get_blackjack_game(game_id)
    if not game_data:
        return

    player_hand = json.loads(game_data['player_hand'])
    dealer_hand = json.loads(game_data['dealer_hand'])
    player_hand_str = " ".join(player_hand)
    player_value = calculate_hand_value(player_hand)
    
    if final:
        dealer_hand_str = " ".join(dealer_hand)
        dealer_value = calculate_hand_value(dealer_hand)
        dealer_label = f" (Value: {dealer_value})"
    else:
        dealer_hand_str = f"{dealer_hand[0]} [?]"
        dealer_value = get_card_value(dealer_hand[0])
        dealer_label = f" (Visible Value: {dealer_value})"

    text = (
        f"🃏 <b>Blackjack Game</b>\n\n"
        f"<b>Your Hand:</b> <code>{player_hand_str}</code> (Value: {player_value})\n"
        f"<b>Dealer's Hand:</b> <code>{dealer_hand_str}</code>{dealer_label}"
    )

    reply_markup = None if final else kb.create_blackjack_keyboard(game_id)
    await edit_or_answer(bot, chat_id, message_id, text, reply_markup=reply_markup, inline_message_id=inline_message_id)



async def blackjack_hit_logic(callback: types.CallbackQuery, game_id: str, game_data: dict):
    deck = json.loads(game_data['deck'])
    player_hand = json.loads(game_data['player_hand'])
    player_hand.append(deal_card(deck))
    player_value = calculate_hand_value(player_hand)

    db.update_blackjack_game(game_id, json.dumps(deck), json.dumps(player_hand), game_data['dealer_hand'], "player_turn")

    if player_value > 21:
        new_balance = db.get_user_balance(game_data['user_id'])
        result_msg = f"You busted with {player_value}! 💀 You got cooked for <b>{game_data['bet_amount']}</b> RP.\nNew balance: <b>{new_balance}</b>."

        player_hand_str = " ".join(player_hand)
        dealer_hand_str = " ".join(json.loads(game_data['dealer_hand']))

        final_text = (
            f"🃏 <b>Blackjack Game (Finished)</b>\n\n"
            f"<b>Your Hand:</b> <code>{player_hand_str}</code> (Value: {player_value})\n"
            f"<b>Dealer's Hand:</b> <code>{dealer_hand_str}</code> (Value: {calculate_hand_value(json.loads(game_data['dealer_hand']))})\n\n"
            f"{result_msg}"
        )

        await edit_or_answer(
            callback.bot,
            callback.message.chat.id if callback.message else None,
            callback.message.message_id if callback.message else None,
            final_text,
            reply_markup=None,
            inline_message_id=callback.inline_message_id
        )
        db.delete_blackjack_game(game_id)
    else:
        await show_blackjack_state(callback.bot, game_id, chat_id=callback.message.chat.id if callback.message else None, message_id=callback.message.message_id if callback.message else None, inline_message_id=callback.inline_message_id)
    
    await callback.answer()

async def blackjack_stand_logic(callback: types.CallbackQuery, game_id: str, game_data: dict):
    deck = json.loads(game_data['deck'])
    dealer_hand = json.loads(game_data['dealer_hand'])
    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand.append(deal_card(deck))

    player_hand = json.loads(game_data['player_hand'])
    player_value = calculate_hand_value(player_hand)
    dealer_value = calculate_hand_value(dealer_hand)

    user_id = game_data['user_id']
    amount = game_data['bet_amount']

    if dealer_value > 21 or player_value > dealer_value:
        db.update_user_balance(user_id, amount * 2)
        new_balance = db.get_user_balance(user_id)
        result_msg = f"W mans! You get <b>{amount * 2}</b> RP. 🍷🗿\nNew balance: <b>{new_balance}</b> RP."
    elif player_value < dealer_value:
        new_balance = db.get_user_balance(user_id)
        result_msg = f"Dealer mogged you. You lost <b>{amount}</b> RP. 📉\nNew balance: <b>{new_balance}</b> RP."
    else:
        db.update_user_balance(user_id, amount)
        new_balance = db.get_user_balance(user_id)
        result_msg = f"It's a push! Your <b>{amount}</b> RP are returned safely. 😮‍💨\nNew balance: <b>{new_balance}</b> RP."

    player_hand_str = " ".join(player_hand)
    dealer_hand_str = " ".join(dealer_hand)

    final_text = (
        f"🃏 <b>Blackjack Game (Finished)</b>\n\n"
        f"<b>Your Hand:</b> <code>{player_hand_str}</code> (Value: {player_value})\n"
        f"<b>Dealer's Hand:</b> <code>{dealer_hand_str}</code> (Value: {dealer_value})\n\n"
        f"{result_msg}"
    )

    await edit_or_answer(
        callback.bot,
        callback.message.chat.id if callback.message else None,
        callback.message.message_id if callback.message else None,
        final_text,
        reply_markup=None,
        inline_message_id=callback.inline_message_id
    )

    db.delete_blackjack_game(game_id)
    await callback.answer()

# --- Coinflip (Single Player Rewrite) --- 

async def start_coinflip(user: types.User, amount: int) -> str | None:
    is_cd, time_left, roast = db.get_cooldown_status(user.id, "coinflip", 7)
    if is_cd:
        return roast

    balance = db.get_user_balance(user.id)

    if amount <= 0:
        return "You can't bet zero or negative points."
    if balance < amount:
        return f"You're too broke for that. You only have <b>{balance}</b> RP."

    db.lock_points(user.id, amount)
    db.update_cooldown(user.id, "coinflip")
    return None

@router.message(Command("coinflip"))
async def coinflip_handler(message: types.Message, command: CommandObject):
    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    if not command.args or not command.args.isdigit():
        await message.reply("Please specify a valid amount for the coinflip!\nUsage: <code>/coinflip &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)
    error_message = await start_coinflip(user, amount)

    if error_message:
        await message.reply(error_message, parse_mode="HTML")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="Heads 🪙", callback_data=f"coinflip:guess:{user.id}:{amount}:heads")
    builder.button(text="Tails 🪙", callback_data=f"coinflip:guess:{user.id}:{amount}:tails")

    user_display_name = get_display_name(user.full_name, user.username)

    await message.reply(
        f"🪙 {user_display_name} started a coinflip for <b>{amount}</b> RP!\n\n"
        f"Pick your side:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("coinflip:guess:"))
async def coinflip_guess_callback(callback: types.CallbackQuery):
    _, _, user_id_str, amount_str, guess = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        return await callback.answer("This is not your coinflip bro. Play your own game!", show_alert=True)

    outcome = random.choice(["heads", "tails"])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Play Again 🪙", callback_data=f"coinflip:replay:{user_id}:{amount}")
    
    if guess == outcome:
        winnings = amount # Profit is the bet amount, total return is bet * 2
        db.update_user_balance(user_id, winnings)
        new_balance = db.get_user_balance(user_id)
        
        await callback.message.edit_text(
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>!\n"
            f"You guessed correctly and secured <b>{amount}</b> RP in profit! {random.choice(WIN_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        new_balance = db.get_user_balance(user_id)
        
        await callback.message.edit_text(
            f"🪙 <b>Coinflip Result!</b>\n\n"
            f"The coin landed on <b>{outcome.capitalize()}</b>.\n"
            f"You guessed wrong and got cooked for <b>{amount}</b> RP. {random.choice(LOSE_EMOJI)}\n\n"
            f"New Balance: <b>{new_balance}</b> RP.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("coinflip:replay:"))
async def coinflip_replay_callback(callback: types.CallbackQuery):
    _, _, user_id_str, amount_str = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        return await callback.answer("This is not your coinflip bro. Play your own game!", show_alert=True)

    error_message = await start_coinflip(callback.from_user, amount)
    if error_message:
        await callback.answer(error_message, show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="Heads 🪙", callback_data=f"coinflip:guess:{user_id}:{amount}:heads")
    builder.button(text="Tails 🪙", callback_data=f"coinflip:guess:{user_id}:{amount}:tails")

    text = f"🪙 You locked in <b>{amount}</b> RP again!\n\nPick your side:"
    await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, text, reply_markup=builder.as_markup(), inline_message_id=callback.inline_message_id)
    await callback.answer()



# --- Heist (Revamped) --- 

@router.message(Command("heist"))
async def heist_handler(message: types.Message, command: CommandObject):
    is_cd, time_left, roast = db.get_cooldown_status(message.from_user.id, "heist", 300)
    if is_cd:
        await message.reply(f"The feds are still watching 🚓. {roast}", parse_mode="HTML")
        return

    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    builder = InlineKeyboardBuilder()
    builder.button(text="Small Heist (Anyone)", callback_data="heist:start:small")
    builder.button(text="Big Heist (300+ RP)", callback_data="heist:start:big")

    await message.reply(
        "🔥 <b>Choose your Heist Target</b> 🔥\n\n"
        "<b>Small Heist:</b> Low risk, low reward. Anyone can join.\n"
        "<b>Big Heist:</b> High risk, massive reward. Requires <b>300+ RP</b> to join.\n\n"
        "⚠️ <i>WARNING: Failing a heist will brutally deduct your RP and can put your balance in the negatives!</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("heist:start:"))
async def heist_start_callback(callback: types.CallbackQuery):
    _, _, heist_type = callback.data.split(':')
    user = callback.from_user
    
    db.add_or_update_user(user.id, user.username, user.full_name)

    if heist_type == "big":
        if db.get_user_balance(user.id) < 300:
            return await callback.answer("You need at least 300 RP to start a Big Heist!", show_alert=True)

    game_id = db.create_game(f'heist_{heist_type}', user.id, 0)
    user_display_name = get_display_name(user.full_name, user.username)
    
    heist_name = "Major BIG HEIST" if heist_type == "big" else "Quick SMALL HEIST"

    await callback.message.edit_text(
        f"🔥 {user_display_name} is plotting a <b>{heist_name}</b>!\n\n"
        f"A squad is forming. You have 2 minutes to lock in!\n"
        f"⚠️ <i>WARNING: Failing a heist will deduct RP and can put you in negative balance!</i>\n"
        f"<b>Requirement:</b> Minimum 2 players.\n\n"
        f"<b>Current Squad:</b>\n- {user_display_name}",
        reply_markup=kb.create_heist_keyboard(game_id),
        parse_mode="HTML"
    )

    asyncio.create_task(heist_timer(callback.bot, callback.message.chat.id, callback.message.message_id, game_id, heist_type))
    db.update_cooldown(user.id, "heist")
    await callback.answer()

async def heist_timer(bot: Bot, chat_id: int, message_id: int, game_id: int, heist_type: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Squad Up! 💰", callback_data=f"heist:join:{game_id}")
    markup = builder.as_markup()

    await asyncio.sleep(60)
    game = db.get_game(game_id)
    if game and game['status'] == 'waiting':
        try:
            await bot.send_message(chat_id, f"⏳ <b>Heist Update:</b> 1 minute left to join the {'Big' if heist_type == 'big' else 'Small'} Heist! We need a minimum of 2 players. Squad up now!", reply_to_message_id=message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass
            
    await asyncio.sleep(30)
    game = db.get_game(game_id)
    if game and game['status'] == 'waiting':
        try:
            await bot.send_message(chat_id, "⏳ <b>Heist Update:</b> 30 seconds left! Last chance to join!", reply_to_message_id=message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass

    await asyncio.sleep(30)
    game = db.get_game(game_id)
    if game and game['status'] == 'waiting':
        await finish_heist(bot, chat_id, message_id, game_id, heist_type)

@router.callback_query(F.data.startswith("heist:join"))
async def heist_join_callback(callback: types.CallbackQuery):
    _, _, game_id_str = callback.data.split(':')
    game_id = int(game_id_str)

    game = db.get_game(game_id)
    if not game or game['status'] != 'waiting':
        return await callback.answer("This heist already happened bro. You missed the train.", show_alert=True)

    joiner = callback.from_user
    
    heist_type = "small"
    if "big" in game['game_type']:
        heist_type = "big"
        
    if heist_type == "big":
        if db.get_user_balance(joiner.id) < 300:
            return await callback.answer("You need at least 300 RP to join a Big Heist! Broke vibes.", show_alert=True)

    crew_ids = db.get_game_players(game_id)

    if joiner.id in crew_ids:
        return await callback.answer("Bro you are already in the squad. Stop spamming.", show_alert=True)

    db.add_or_update_user(joiner.id, joiner.username, joiner.full_name)
    db.add_player_to_game(game_id, joiner.id)

    updated_crew_ids = db.get_game_players(game_id)
    crew_names = []
    for user_id in updated_crew_ids:
        user_info = db.get_user_info(user_id)
        if user_info:
            crew_names.append(get_display_name(user_info[0], user_info[1]))

    crew_list_str = "\n".join(f"- {name}" for name in crew_names)
    heist_starter_info = db.get_user_info(game['creator_id'])
    starter_name = get_display_name(heist_starter_info[0], heist_starter_info[1])

    heist_name = "Major BIG HEIST" if heist_type == "big" else "Quick SMALL HEIST"

    new_text = (
        f"🔥 {starter_name} is plotting a <b>{heist_name}</b>!\n\n"
        f"A squad is forming. You have 2 minutes to lock in!\n"
        f"⚠️ <i>WARNING: Failing a heist will deduct RP and can put you in negative balance!</i>\n"
        f"<b>Requirement:</b> Minimum 2 players.\n\n"
        f"<b>Current Squad ({len(updated_crew_ids)}):</b>\n{crew_list_str}"
    )

    try:
        await callback.message.edit_text(
            new_text,
            reply_markup=callback.message.reply_markup,
            parse_mode="HTML"
        )
        await callback.answer("You locked in. Squad up!", show_alert=True)
    except Exception as e:
        print(f"Failed to edit heist message: {e}")
        await callback.answer("Joined the crew, but couldn't update the original message.", show_alert=True)

@router.message(Command("join"))
async def join_handler(message: types.Message):
    open_heist = db.get_open_heist_game()
    if not open_heist:
        await message.reply("There are no open heists right now. Start one yourself with <code>/heist</code>!", parse_mode="HTML")
        return
        
    game_id = open_heist['game_id']
    joiner = message.from_user
    
    heist_type = "small"
    if "big" in open_heist['game_type']:
        heist_type = "big"
        
    if heist_type == "big" and db.get_user_balance(joiner.id) < 300:
        await message.reply("You need at least 300 RP to join a Big Heist! Broke vibes.", parse_mode="HTML")
        return

    crew_ids = db.get_game_players(game_id)
    if joiner.id in crew_ids:
        await message.reply("Bro you are already in the squad. Just wait for it to start.", parse_mode="HTML")
        return

    db.add_or_update_user(joiner.id, joiner.username, joiner.full_name)
    db.add_player_to_game(game_id, joiner.id)
    
    await message.reply("✅ You successfully locked in for the heist! Squad up!", parse_mode="HTML")

async def finish_heist(bot: Bot, chat_id: int, message_id: int, game_id: int, heist_type: str):
    db.update_game_status(game_id, 'finished')
    
    crew_ids = db.get_game_players(game_id)
    if len(crew_ids) < 2:
        try:
            await bot.edit_message_text(f"The heist was called off! We needed a minimum of <b>2</b> players, but only {len(crew_ids)} showed up. The squad abandoned the plan. Negative aura. 💀", chat_id, message_id, parse_mode="HTML")
        except Exception as e:
            pass
        return

    total_rizz = sum(db.get_user_balance(user_id) for user_id in crew_ids)
    
    success_chance = min(total_rizz / 40000, 0.50) if heist_type == 'big' else min(total_rizz / 20000, 0.85)
    roll = random.random()

    base_payout = random.randint(500, 1500) if heist_type == 'big' else random.randint(100, 300)
    base_loss = random.randint(300, 800) if heist_type == 'big' else random.randint(50, 200)

    crew_details = {uid: get_display_name(db.get_user_info(uid)[0], db.get_user_info(uid)[1]) for uid in crew_ids}

    if roll < (success_chance * 0.5):
        for user_id in crew_ids: db.update_user_balance(user_id, base_payout)
        crew_members_str = "\n".join(f"- {name}" for name in crew_details.values())
        
        result_msg = (
            f"✅ <b>{heist_type.upper()} HEIST - FLAWLESS VICTORY!</b> ✅\n\n"
            f"The squad executed perfectly! The aura was unmatched.\n"
            f"Everyone grabbed a massive cut of <b>{base_payout}</b> RP!\n\n"
            f"<b>The Goats:</b>\n{crew_members_str}"
        )

    elif roll < success_chance:
        num_escaped = max(1, len(crew_ids) // 2)
        escaped_ids = random.sample(crew_ids, num_escaped)
        busted_ids = [uid for uid in crew_ids if uid not in escaped_ids]

        escaped_str = "\n".join(f"- {crew_details[uid]} (+{base_payout} RP)" for uid in escaped_ids)
        busted_str = "\n".join(f"- {crew_details[uid]} (-{base_loss} RP)" for uid in busted_ids)

        for uid in escaped_ids: db.update_user_balance(uid, base_payout)
        for uid in busted_ids: db.update_user_balance(uid, -base_loss)

        result_msg = (
            f"⚠️ <b>{heist_type.upper()} HEIST - MESSY GETAWAY!</b> ⚠️\n\n"
            f"The alarm got tripped! Some of the squad escaped with the bag, but the others got caught by the feds!\n\n"
            f"<b>Escaped with the Bag:</b>\n{escaped_str}\n\n"
            f"<b>Caught & Penalized:</b>\n{busted_str}"
        )

    else:
        for user_id in crew_ids: db.update_user_balance(user_id, -base_loss)
        crew_members_str = "\n".join(f"- {name}" for name in crew_details.values())
        
        result_msg = (
            f"❌ <b>{heist_type.upper()} HEIST FAILED!</b> ❌\n\n"
            f"The squad got entirely caught lackin'! The mission was an absolute flop.\n"
            f"Each member is heavily penalized and loses <b>{base_loss}</b> RP. 📉\n\n"
            f"<b>The Clowns:</b>\n{crew_members_str}"
        )

    try:
        await bot.send_message(chat_id, result_msg, reply_to_message_id=message_id, parse_mode="HTML")
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
    except Exception as e:
        pass

# --- Lottery ---

@router.message(Command("lottery"))
async def lottery_handler(message: types.Message):
    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    balance = db.get_user_balance(user.id)
    price = 50

    time_info = db.get_time_until_lottery()
    
    if balance < price:
        await message.reply(f"You need <b>{price}</b> RP to buy a lottery ticket. You only have <b>{balance}</b>. Keep grinding lil bro.", parse_mode="HTML")
        return

    db.buy_lottery_ticket(user.id, message.chat.id, price)
    
    if time_info:
        hours, minutes = time_info
        time_text = f"⏳ <b>Time left until draw:</b> {hours}h {minutes}m"
    else:
        time_text = "⏳ <b>The 24-hour countdown for the grand draw starts exactly NOW!</b>"

    await message.reply(
        f"🎟️ <b>TICKET SECURED</b> 🎟️\n\n"
        f"You successfully copped a lottery ticket for <b>50</b> RP!\n"
        f"<i>Every ticket bought adds +50 RP to the massive grand prize pool!</i>\n\n"
        f"{time_text}", 
        parse_mode="HTML"
    )

async def draw_lottery_winner(bot: Bot):
    all_tickets = db.get_all_lottery_tickets()
    if not all_tickets:
        return 

    pot = len(all_tickets) * 50
    winner_ticket = random.choice(all_tickets)
    winner_id = winner_ticket[0]

    db.update_user_balance(winner_id, pot)
    
    winner_info = db.get_user_info(winner_id)
    if not winner_info:
        db.clear_lottery_tickets() 
        return

    winner_name = get_display_name(winner_info[0], winner_info[1])

    announcement = (
        f"🎟️ <b>LOTTERY DRAW!</b> 🎟️\n\n"
        f"The winning ticket belongs to the absolute Top G: <b>{escape_html(winner_name)}</b>!\n\n"
        f"They just bagged the grand prize of <b>{pot}</b> Rizz Points! Congratulations! {random.choice(WIN_EMOJI)}"
    )

    chat_ids = {ticket[1] for ticket in all_tickets}

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, announcement, parse_mode="HTML")
        except Exception as e:
            pass
    
    db.clear_lottery_tickets()