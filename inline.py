from aiogram import Router, types, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder
from games import start_slots, start_blackjack, start_coinflip, process_slots, show_blackjack_state
from handlers import escape_html, get_display_name, start_gamble, run_gamble_logic, GAMBLE_WINS, GAMBLE_LOSSES, WIN_EMOJI, LOSE_EMOJI, edit_or_answer
import database as db
import keyboards as kb
import random

router = Router()

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="10", callback_data="inline_slots:10")
    builder.button(text="25", callback_data="inline_slots:25")
    builder.button(text="50", callback_data="inline_slots:50")
    builder.button(text="100", callback_data="inline_slots:100")

    blackjack_builder = InlineKeyboardBuilder()
    blackjack_builder.button(text="10", callback_data="inline_blackjack:10")
    blackjack_builder.button(text="25", callback_data="inline_blackjack:25")
    blackjack_builder.button(text="50", callback_data="inline_blackjack:50")
    blackjack_builder.button(text="100", callback_data="inline_blackjack:100")

    coinflip_builder = InlineKeyboardBuilder()
    coinflip_builder.button(text="10", callback_data="inline_coinflip:10")
    coinflip_builder.button(text="25", callback_data="inline_coinflip:25")
    coinflip_builder.button(text="50", callback_data="inline_coinflip:50")
    coinflip_builder.button(text="100", callback_data="inline_coinflip:100")

    gamble_builder = InlineKeyboardBuilder()
    gamble_builder.button(text="10", callback_data="inline_gamble:10")
    gamble_builder.button(text="25", callback_data="inline_gamble:25")
    gamble_builder.button(text="50", callback_data="inline_gamble:50")
    gamble_builder.button(text="100", callback_data="inline_gamble:100")

    fight_builder = InlineKeyboardBuilder()
    fight_builder.button(text="Start a Public Fight!", callback_data="inline_fight:start")

    results = [
        InlineQueryResultArticle(
            id="slots",
            title="Slots",
            input_message_content=InputTextMessageContent(
                message_text="Select a bet amount for slots:"
            ),
            reply_markup=builder.as_markup(),
            description="Play the slot machine.",
        ),
        InlineQueryResultArticle(
            id="blackjack",
            title="Blackjack",
            input_message_content=InputTextMessageContent(
                message_text="Select a bet amount for blackjack:"
            ),
            reply_markup=blackjack_builder.as_markup(),
            description="Play a game of Blackjack.",
        ),
        InlineQueryResultArticle(
            id="coinflip",
            title="Coinflip",
            input_message_content=InputTextMessageContent(
                message_text="Select a bet amount for coinflip:"
            ),
            reply_markup=coinflip_builder.as_markup(),
            description="Start or join a coinflip.",
        ),
        InlineQueryResultArticle(
            id="gamble",
            title="Gamble",
            input_message_content=InputTextMessageContent(
                message_text="Select a bet amount for gamble:"
            ),
            reply_markup=gamble_builder.as_markup(),
            description="A 50/50 chance to double your bet.",
        ),
        InlineQueryResultArticle(
            id="public_fight",
            title="Public Fight",
            input_message_content=InputTextMessageContent(
                message_text="Start a public fight where anyone can join!"
            ),
            reply_markup=fight_builder.as_markup(),
            description="Wager 100 RP in a public fight.",
        ),
        InlineQueryResultArticle(
            id="heist",
            title="Heist",
            input_message_content=InputTextMessageContent(
                message_text="Start a heist by using the `/heist` command!"
            ),
            description="Start a massive group heist.",
        ),
        InlineQueryResultArticle(
            id="lottery",
            title="Lottery",
            input_message_content=InputTextMessageContent(
                message_text="Buy a lottery ticket by using the `/lottery` command!"
            ),
            description="Buy a ticket for the daily draw.",
        ),
    ]
    await query.answer(results, cache_time=1)

@router.callback_query(F.data.startswith("inline_slots:"))
async def inline_slots_callback(callback: types.CallbackQuery):
    amount = int(callback.data.split(":")[1])
    user = callback.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)
    
    error_message = await start_slots(user, amount)
    if error_message:
        await callback.answer(error_message, show_alert=True)
        return

    await edit_or_answer(callback.bot, None, None, "Spinning the slots...", inline_message_id=callback.inline_message_id)
    await process_slots(callback.bot, user, amount, inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("inline_blackjack:"))
async def inline_blackjack_callback(callback: types.CallbackQuery):
    amount = int(callback.data.split(":")[1])
    user = callback.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    game_id = f"blackjack_{callback.inline_message_id}"
    error_message, game_state = await start_blackjack(user, amount, game_id)

    if error_message:
        await callback.answer(error_message, show_alert=True)
        return

    await edit_or_answer(callback.bot, None, None, f"Starting blackjack for <b>{amount}</b> RP... Let him cook! 🃏", inline_message_id=callback.inline_message_id)
    await show_blackjack_state(callback.bot, game_id, inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("inline_coinflip:"))
async def inline_coinflip_callback(callback: types.CallbackQuery):
    amount = int(callback.data.split(":")[1])
    user = callback.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    error_message = await start_coinflip(user, amount)
    if error_message:
        await callback.answer(error_message, show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="Heads 🪙", callback_data=f"coinflip:guess:{user.id}:{amount}:heads")
    builder.button(text="Tails 🪙", callback_data=f"coinflip:guess:{user.id}:{amount}:tails")

    user_display_name = escape_html(get_display_name(user.full_name, user.username))

    text = f"🪙 {user_display_name} started a coinflip for <b>{amount}</b> RP!\n\nPick your side:"
    await edit_or_answer(callback.bot, None, None, text, reply_markup=builder.as_markup(), inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("inline_gamble:"))
async def inline_gamble_callback(callback: types.CallbackQuery):
    amount = int(callback.data.split(":")[1])
    user = callback.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    error_message = await start_gamble(user, amount)
    if error_message:
        await callback.answer(error_message, show_alert=True)
        return

    is_win, new_balance = run_gamble_logic(user.id, amount)

    if is_win:
        response_text = random.choice(GAMBLE_WINS).format(amount=amount, emoji=random.choice(WIN_EMOJI))
    else:
        response_text = random.choice(GAMBLE_LOSSES).format(amount=amount, emoji=random.choice(LOSE_EMOJI))

    text = f"{response_text}\n\nYour new balance: <b>{new_balance}</b> RP."
    await edit_or_answer(callback.bot, None, None, text, inline_message_id=callback.inline_message_id)
    await callback.answer()

@router.callback_query(F.data == "inline_fight:start")
async def inline_fight_start_callback(callback: types.CallbackQuery):
    user = callback.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    challenge_id = db.create_public_challenge(user.id, "brawl", 100, None, None)
    user_display_name = escape_html(get_display_name(user.full_name, user.username))

    text = f"🥊 {user_display_name} has started a public fight for 100 RP!\n\nAnyone can accept this challenge!"
    reply_markup = kb.create_public_challenge_keyboard(challenge_id)

    await edit_or_answer(callback.bot, None, None, text, reply_markup=reply_markup, inline_message_id=callback.inline_message_id)
    await callback.answer()
