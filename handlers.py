import random
import json
import math
from aiogram import Router, F, types, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.enums import MessageEntityType

from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
from utils import get_display_name, escape_html
from games import blackjack_callback_handler
from shared import WIN_EMOJI, LOSE_EMOJI, edit_or_answer


router = Router()

# --- Response Lists ---

GAMBLE_WINS = [
    "POGGERS! You locked in and it paid off! You won <b>{amount}</b> RP! Certified W. {emoji}",
    "Aura is off the charts. You just hit the jackpot for <b>{amount}</b> RP! {emoji}",
    "Bro is literally him. Secured <b>{amount}</b> RP from the gamble! {emoji}"
]
GAMBLE_LOSSES = [
    "Oof. You got cooked 🍳. Lost <b>{amount}</b> RP. Should've just trusted your gut, my guy. {emoji}",
    "The house always wins. Bro lost <b>{amount}</b> RP. Negative aura behavior. {emoji}",
    "Bro fumbled the bag 💀. Say goodbye to <b>{amount}</b> RP. {emoji}"
]
DAILY_CLAIM_SUCCESS = [
    "Your daily dose of aura has arrived! You bagged <b>{amount}</b> RP. Go cook. {emoji}",
    "The Rizz Gods have blessed you. Here's <b>{amount}</b> RP. Absolute cinema. {emoji}",
    "Bro just looksmaxed for the day. <b>{amount}</b> RP added to the stash! {emoji}"
]

FIGHT_WINNER = [
    "In a legendary clash of auras, {winner_name} completely mogged {loser_name} and stole <b>{amount}</b> RP! Absolute cinema. {emoji}",
    "It's over! {winner_name} cooked {loser_name} and snatched <b>{amount}</b> RP. A true sigma. {emoji}",
    "Bro didn't even stand a chance. {winner_name} wiped the floor with {loser_name} for <b>{amount}</b> RP. {emoji}"
]

async def get_target_user(message: Message) -> types.User | None:
    if message.reply_to_message and message.reply_to_message.from_user and not message.reply_to_message.from_user.is_bot:
        return message.reply_to_message.from_user
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.TEXT_MENTION and entity.user:
                return entity.user
    return None

@router.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    is_new_user = db.add_or_update_user(user.id, user.username, user.full_name)
    display_name = escape_html(get_display_name(user.full_name, user.username))

    if is_new_user:
        welcome_text = (
            f"Wsg chat, {display_name}! Welcome to the <b>Rizz Economy</b> 👑.\n\n"
            f"You've been blessed with <b>100</b> starting Rizz Points. Time to stop being an NPC and start looksmaxxing.\n\n"
            f"Use /help to see all the commands and start cooking!"
        )
    else:
        balance = db.get_user_balance(user.id)
        welcome_text = (
            f"Welcome back, {display_name}!\n\n"
            f"Your current stash is <b>{balance}</b> Rizz Points. Keep on grinding! 🔥"
        )
    await message.reply(welcome_text, parse_mode="HTML")

@router.message(Command("help", "cmds"))
async def help_handler(message: Message):
    db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    help_text = (
        "👑 <b>Welcome to the Rizz Casino!</b> 👑\n"
        "Here are all the ways to cook and increase your aura:\n\n"
        "<b>---- Main Commands ----</b>\n"
        "<code>/start</code> - Initialize or welcome back to the bot.\n"
        "<code>/help</code> - Shows this exact message.\n"
        "<code>/rizz</code> - View your detailed Rizz Profile.\n"
        "<code>/balance</code> - Quick aura check (RP Balance).\n"
        "<code>/leaderboard</code> - See the top Rizz Kings.\n"
        "<code>/grow</code> or <code>/daily</code> - Claim your daily free aura bonus.\n"
        "<code>/beg</code> - Beg for change (1 hour cooldown).\n\n"
        "💸 <b>Economy & Social</b>\n"
        "<code>/transfer &lt;@user&gt; &lt;amount&gt;</code> - Slide points to the homies (67% tax).\n"
        "<code>/shop</code> - Cop items to boost your aura.\n"
        "<code>/loan &lt;amount&gt;</code> - Take out a loan (50% interest, 7-day term).\n"
        "<code>/payloan &lt;amount&gt;</code> - Pay back your debt.\n\n"
        "🎲 <b>Gamblecore (Single-Player)</b>\n"
        "<code>/gamble &lt;amount&gt;</code> - A 50/50 chance to double your bet.\n"
        "<code>/slots &lt;amount&gt;</code> - Spin the slots. Triple diamonds = 10x!\n"
        "<code>/coinflip &lt;amount&gt;</code> - Bet on Heads or Tails.\n\n"
        "⚔️ <b>Multiplayer & Co-op</b>\n"
        "<code>/heist</code> - Form a squad for a high-risk, high-reward heist.\n"
        "<code>/join</code> - Join the latest active heist or lobby.\n"
        "<code>/fight &lt;@user&gt; &lt;amount&gt;</code> - Challenge a user to an aura duel.\n\n"
        "🎟️ <b>Lottery</b>\n"
        "<code>/lottery</code> - Buy a ticket for the daily grand prize draw (50 RP)."
    )
    await message.reply(help_text, parse_mode="HTML")

@router.message(Command("balance"))
async def balance_handler(message: Message):
    db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    balance = db.get_user_balance(message.from_user.id)
    await message.reply(f"Your current balance is <b>{balance}</b> Rizz Points. Keep maxxing. 💪", parse_mode="HTML")

@router.message(Command("leaderboard"))
async def leaderboard_handler(message: Message):
    db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    page = 1
    total_users, leaderboard_page = db.get_leaderboard_paginated(page, 10)
    
    if not leaderboard_page:
        return await message.reply("The leaderboard is completely dead. No one has any aura yet. 💀", parse_mode="HTML")
    
    response = "🏆 <b>Top Gs / Aura Leaderboard</b> 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (name, points) in enumerate(leaderboard_page):
        rank = i + 1
        medal = medals[i] if rank <= 3 else f"<b>#{rank}</b>"
        response += f"{medal} {escape_html(name)} - <b>{points}</b> RP\n"
        
    total_pages = math.ceil(total_users / 10)
    markup = kb.create_leaderboard_keyboard(page, total_pages) if total_pages > 1 else None
    
    await message.reply(response, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("leaderboard:page:"))
async def leaderboard_page_callback(callback: CallbackQuery):
    _, _, page_str = callback.data.split(':')
    page = int(page_str)
    
    total_users, leaderboard_page = db.get_leaderboard_paginated(page, 10)
    if not leaderboard_page:
        return await callback.answer("No more users.", show_alert=True)
        
    response = f"🏆 <b>Top Gs / Aura Leaderboard (Page {page})</b> 🏆\n\n"
    offset = (page - 1) * 10
    
    for i, (name, points) in enumerate(leaderboard_page):
        rank = offset + i + 1
        medal = f"<b>#{rank}</b>"
        response += f"{medal} {escape_html(name)} - <b>{points}</b> RP\n"
        
    total_pages = math.ceil(total_users / 10)
    markup = kb.create_leaderboard_keyboard(page, total_pages)
    
    await callback.message.edit_text(response, reply_markup=markup, parse_mode="HTML")
    await callback.answer()

@router.message(Command("grow", "daily", "claim"))
async def daily_handler(message: Message):
    user_id = message.from_user.id
    db.add_or_update_user(user_id, message.from_user.username, message.from_user.full_name)

    can_claim, hours_left, mins_left = db.get_daily_status(user_id)

    if can_claim:
        base_amount = random.randint(25, 75)
        bonus_amount = 0

        user_items = db.get_user_items(user_id)
        for item in user_items:
            try:
                effect_data = json.loads(item['effect'])
                if effect_data.get('effect') == 'permanent_daily_increase':
                    bonus_amount += effect_data.get('amount', 0)
            except (json.JSONDecodeError, TypeError):
                continue

        total_amount = base_amount + bonus_amount
        db.claim_daily(user_id, total_amount)

        response = random.choice(DAILY_CLAIM_SUCCESS).format(amount=total_amount, emoji=random.choice(WIN_EMOJI))
        if bonus_amount > 0:
            response += f"\n<i>(Includes a bonus of {bonus_amount} RP from your shop items! W investments.)</i>"

        new_balance = db.get_user_balance(user_id)
        await message.reply(f"{response}\n\nYour new balance: <b>{new_balance}</b> RP.", parse_mode="HTML")
    else:
        await message.reply(f"Chill out lil bro, you're on cooldown. You can claim your next aura boost in <b>{hours_left}h {mins_left}m</b>. Touch grass until then.", parse_mode="HTML")

@router.message(Command("beg"))
async def beg_handler(message: Message):
    user_id = message.from_user.id
    db.add_or_update_user(user_id, message.from_user.username, message.from_user.full_name)

    is_cd, time_left, roast = db.get_cooldown_status(user_id, "beg", 3600) 
    if is_cd:
        minutes = time_left // 60
        await message.reply(f"Bro is literally on his knees begging 💀. Have some self respect. The streets will ignore you for another <b>{minutes} minutes</b>.", parse_mode="HTML")
        return

    amount = random.randint(1, 10)
    db.update_user_balance(user_id, amount)
    db.update_cooldown(user_id, "beg")
    
    await message.reply(f"A passing stranger felt pity for your negative aura and tossed you <b>{amount}</b> RP. Don't spend it all in one place.", parse_mode="HTML")

@router.message(Command("rizz"))
async def rizz_handler(message: Message, command: CommandObject):
    is_cd, time_left, roast = db.get_cooldown_status(message.from_user.id, "rizz", 3)
    if is_cd:
        await message.reply(roast, parse_mode="HTML")
        return

    initiator_user = message.from_user
    db.add_or_update_user(initiator_user.id, initiator_user.username, initiator_user.full_name)
    target_user = await get_target_user(message)

    if not command.args and not target_user:
        stats = db.get_user_stats(initiator_user.id)
        rank = db.get_user_rank(initiator_user.id)

        if not stats:
            await message.reply("Could not find your stats. Are you even registered bro?", parse_mode="HTML")
            return

        rank_str = f"#{rank}" if rank else "Unranked"

        # Expanded Aura Levels for larger groups (Ensures minimal overlap)
        if not rank or stats['points'] < 0:
            aura = "Negative Aura / Cooked 📉"
        elif rank == 1:
            aura = "The Honored One / Supreme Sigma 👑"
        elif rank == 2:
            aura = "Right Hand of the Rizz / Vice-Sigma ⚜️"
        elif rank == 3:
            aura = "Bronze Giga Chad 🥉"
        elif rank <= 5:
            aura = "Certified Mogger 🤫🧏‍♂️"
        elif rank <= 10:
            aura = "W Aura / Top 10 🍷🗿"
        elif rank <= 15:
            aura = "Rizzly Bear 🐻"
        elif rank <= 20:
            aura = "Skibidi Boss 🚽"
        elif rank <= 25:
            aura = "Looksmaxxing Intern 🪒"
        elif rank <= 30:
            aura = "Edge Lord ⚔️"
        elif rank <= 40:
            aura = "Ohio Survivor 🌽"
        elif rank <= 50:
            aura = "Grimace Shake Victim 🟣"
        elif rank <= 75:
            aura = "Aura Warrior ✨"
        else:
            aura = "Base Form / NPC 🚶‍♂️"
            
        total_games = stats['wins'] + stats['losses']
        win_rate = (stats['wins'] / total_games * 100) if total_games > 0 else 0
        win_rate_str = f"{win_rate:.2f}"

        active_loan = db.get_active_loan(initiator_user.id)
        loan_str = f"<b>{active_loan['outstanding_balance']}</b> RP (In Debt 💀)" if active_loan else "Zero debt. W."

        profile_text = (
            f"👑 <b>Rizz Profile: {escape_html(get_display_name(initiator_user.full_name, initiator_user.username))}</b>\n\n"
            f"🔮 <b>Aura Level:</b> {aura}\n"
            f"🏆 <b>Global Rank:</b> {rank_str}\n"
            f"✨ <b>Rizz Points:</b> {stats['points']} RP\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🥊 <b>1v1 Brawl Stats:</b>\n"
            f"⚔️ <b>W/L (Mogged/Cooked):</b> {stats['wins']} W / {stats['losses']} L\n"
            f"🎯 <b>Win Rate:</b> {win_rate_str}%\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💸 <b>Financials:</b>\n"
            f"🏦 <b>Current Loan:</b> {loan_str}"
        )
        await message.reply(profile_text, parse_mode="HTML")
        db.update_cooldown(message.from_user.id, "rizz")
        return

    if command.args:
        args = command.args.split()
        sub_command = args[0].lower()

        if sub_command == "random":
            random_opponent = db.get_random_user(exclude_id=initiator_user.id)
            if not random_opponent:
                await message.reply("Couldn't find anyone to fight. The server is completely empty, lmao 💀.", parse_mode="HTML")
                return
            
            random_user_obj = types.User(id=random_opponent[0], is_bot=False, first_name=random_opponent[2])
            amount = random.randint(5, 20)
            mock_command = CommandObject(prefix="/", command="fight", args=str(amount))
            
            await message.reply(f"You're challenging a random NPC: <b>{escape_html(random_user_obj.full_name)}</b>! Let him cook.", parse_mode="HTML")
            await process_fight(message, mock_command, random_user_obj)
            db.update_cooldown(message.from_user.id, "rizz")
            return

        if sub_command == "gamble":
            new_args = " ".join(args[1:])
            mock_command = CommandObject(prefix="/", command="gamble", args=new_args)
            await gamble_handler(message, mock_command)
            db.update_cooldown(message.from_user.id, "rizz")
            return
        
        if sub_command == "fight":
            new_args = " ".join(args[1:])
            mock_command = CommandObject(prefix="/", command="fight", args=new_args)
            target_user = await get_target_user(message)
            await process_fight(message, mock_command, target_user)
            db.update_cooldown(message.from_user.id, "rizz")
            return

    if target_user:
        amount = random.randint(10, 30)
        mock_command = CommandObject(prefix="/", command="fight", args=str(amount))
        await process_fight(message, mock_command, target_user)
        db.update_cooldown(message.from_user.id, "rizz")
        return

    await help_handler(message)
    db.update_cooldown(message.from_user.id, "rizz")


async def start_gamble(user: types.User, amount: int) -> str | None:
    is_cd, time_left, roast = db.get_cooldown_status(user.id, "gamble", 5)
    if is_cd:
        return roast

    balance = db.get_user_balance(user.id)

    if amount <= 0:
        return "You can't bet zero or negative points, you absolute NPC."
    if balance < amount:
        return f"LMAO, bro is broke 😭. You only have <b>{balance}</b> RP."

    db.update_cooldown(user.id, "gamble")
    return None

def run_gamble_logic(user_id: int, amount: int) -> tuple[bool, int]:
    if random.choice([True, False]):
        db.update_user_balance(user_id, amount)
        new_balance = db.get_user_balance(user_id)
        return True, new_balance
    else:
        db.update_user_balance(user_id, -amount)
        new_balance = db.get_user_balance(user_id)
        return False, new_balance

@router.message(Command("gamble"))
async def gamble_handler(message: Message, command: CommandObject):
    initiator_user = message.from_user
    db.add_or_update_user(initiator_user.id, initiator_user.username, initiator_user.full_name)
    
    if not command.args or not command.args.isdigit():
        await message.reply("Please specify a valid amount to gamble!\nUsage: <code>/gamble &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)
    error_message = await start_gamble(initiator_user, amount)

    if error_message:
        await message.reply(error_message, parse_mode="HTML")
        return

    is_win, new_balance = run_gamble_logic(initiator_user.id, amount)

    if is_win:
        response_text = random.choice(GAMBLE_WINS).format(amount=amount, emoji=random.choice(WIN_EMOJI))
        await message.reply(f"{response_text}\n\nYour new balance: <b>{new_balance}</b> RP.", 
                            reply_markup=kb.create_gamble_keyboard(initiator_user.id, amount),
                            parse_mode="HTML")
    else:
        response_text = random.choice(GAMBLE_LOSSES).format(amount=amount, emoji=random.choice(LOSE_EMOJI))
        await message.reply(f"{response_text}\n\nYour new balance: <b>{new_balance}</b> RP.", 
                            reply_markup=kb.create_gamble_keyboard(initiator_user.id, amount),
                            parse_mode="HTML")


async def process_fight(message: Message, command: CommandObject, target_user: types.User | None):
    initiator_user = message.from_user
    amount_str = None
    if command.args:
        args = command.args.split()
        amount_str = next((arg for arg in args if arg.isdigit()), None)
    
    if not amount_str:
        amount = random.randint(1, 30)
    else:
        amount = int(amount_str)
    
    if not target_user or target_user.id == initiator_user.id:
        initiator_name = get_display_name(initiator_user.full_name, initiator_user.username)
        sent_message = await message.reply(
            f"📢 {escape_html(initiator_name)} just started a public brawl for <b>{amount}</b> RP! Who's stepping up?",
            parse_mode="HTML"
        )
        challenge_id = db.create_public_challenge(initiator_user.id, "fight", amount, sent_message.message_id, sent_message.chat.id)
        await sent_message.edit_reply_markup(reply_markup=kb.create_public_challenge_keyboard(challenge_id))
        return

    db.add_or_update_user(target_user.id, target_user.username, target_user.full_name)
    challenger_balance = db.get_user_balance(initiator_user.id)
    if amount <= 0:
        await message.reply("You can't fight for 0 or negative rizz, that's just negative aura behavior.", parse_mode="HTML")
        return
    if challenger_balance < amount:
        await message.reply(f"Bro you don't even have enough points to start this. You need {amount}, you only have <b>{challenger_balance}</b> RP 💀.", parse_mode="HTML")
        return
    
    opponent_balance = db.get_user_balance(target_user.id)
    if opponent_balance < amount:
        opponent_name = get_display_name(target_user.full_name, target_user.username)
        await message.reply(f"{escape_html(opponent_name)} is literally too poor to accept. They only have <b>{opponent_balance}</b> RP 😭.", parse_mode="HTML")
        return

    initiator_name = get_display_name(initiator_user.full_name, initiator_user.username)
    target_name = get_display_name(target_user.full_name, target_user.username)
    await message.reply(
        f"Yo {escape_html(target_name)}! {escape_html(initiator_name)} just challenged you to an aura duel for <b>{amount}</b> RP! Do you accept or are you ducking?",
        reply_markup=kb.create_fight_keyboard(initiator_user.id, target_user.id, amount),
        parse_mode="HTML"
    )

@router.message(Command("fight"))
async def fight_handler(message: Message, command: CommandObject):
    is_cd, time_left, roast = db.get_cooldown_status(message.from_user.id, "fight", 5)
    if is_cd:
        await message.reply(roast, parse_mode="HTML")
        return

    db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    target_user = await get_target_user(message)
    await process_fight(message, command, target_user)
    db.update_cooldown(message.from_user.id, "fight")

@router.message(Command("loan"))
async def loan_handler(message: Message, command: CommandObject):
    is_cd, time_left, roast = db.get_cooldown_status(message.from_user.id, "loan", 5)
    if is_cd:
        await message.reply(roast, parse_mode="HTML")
        return

    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    balance = db.get_user_balance(user.id)
    max_loan = int(500 + (balance * 0.15))
    min_loan = 100

    if not command.args or not command.args.isdigit():
        await message.reply("Incorrect format. Usage: <code>/loan &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)

    if amount < min_loan:
        await message.reply(f"The bank won't bother with anything less than <b>{min_loan}</b> RP.", parse_mode="HTML")
        return

    if amount > max_loan:
        await message.reply(f"Based on your current broke status, you can only borrow a maximum of <b>{max_loan}</b> RP.", parse_mode="HTML")
        return

    if db.take_loan(user.id, amount, 0.5, 7):
        new_balance = db.get_user_balance(user.id)
        interest = int(amount * 0.5)
        await message.reply(
            f"You have secured a loan of <b>{amount}</b> RP. \n\n"
            f"⚠️ You must pay back <b>{amount + interest}</b> RP within 7 days or your aura gets seized.\n\n"
            f"New Balance: <b>{new_balance}</b> RP.",
            parse_mode="HTML"
        )
    else:
        await message.reply("Bro, you already have an outstanding loan. Pay your debts before begging for more! 💀", parse_mode="HTML")
    db.update_cooldown(user.id, "loan")

@router.message(Command("payloan"))
async def payloan_handler(message: Message, command: CommandObject):
    is_cd, time_left, roast = db.get_cooldown_status(message.from_user.id, "payloan", 5)
    if is_cd:
        await message.reply(roast, parse_mode="HTML")
        return

    user = message.from_user
    db.add_or_update_user(user.id, user.username, user.full_name)

    if not command.args or not command.args.isdigit():
        await message.reply("Incorrect format. Usage: <code>/payloan &lt;amount&gt;</code>", parse_mode="HTML")
        return

    amount = int(command.args)
    balance = db.get_user_balance(user.id)

    if amount <= 0:
        await message.reply("You have to pay a positive amount. Quit playing with the bank.", parse_mode="HTML")
        return
    
    if balance < amount:
        await message.reply(f"Bro you only have <b>{balance}</b> RP. You can't pay more than you own!", parse_mode="HTML")
        return

    result_message = db.pay_loan(user.id, amount)
    await message.reply(escape_html(result_message), parse_mode="HTML")
    db.update_cooldown(user.id, "payloan")

@router.callback_query(F.data.startswith("action:"))
async def action_callback_handler(callback: CallbackQuery):
    action_id = callback.data.split(':')[1]
    action_data = db.get_action_data(action_id)

    if not action_data:
        await callback.answer("This action is expired or invalid.", show_alert=True)
        return

    action_type = action_data.get('action_type')
    data = action_data.get('data')

    if action_type == 'fight':
        await handle_fight_action(callback, data)
    elif action_type == 'blackjack':
        game_id = data.get('game_id')
        move = data.get('move')
        await blackjack_callback_handler(callback, game_id, move)
    else:
        await callback.answer("Unknown action type.", show_alert=True)

async def handle_fight_action(callback: CallbackQuery, data: dict):
    action = callback.data.split(':')[2]
    challenger_id = data['challenger_id']
    opponent_id = data['opponent_id']
    amount = data['amount']

    if callback.from_user.id != opponent_id:
        await callback.answer("This duel isn't for you. Stop being a third wheel.", show_alert=True)
        return
    
    challenger_info = db.get_user_info(challenger_id)
    opponent_info = db.get_user_info(opponent_id)
    if not challenger_info or not opponent_info:
        await callback.message.edit_text("Error: Can't find the fighters.", parse_mode="HTML")
        return

    challenger_name = get_display_name(challenger_info[0], challenger_info[1])
    opponent_name = get_display_name(opponent_info[0], opponent_info[1])

    if action == "decline":
        await callback.message.edit_text(f"Bro ducked the fade 🏃💨. {escape_html(opponent_name)} declined the fight. {escape_html(challenger_name)} keeps their {amount} RP... for now.", parse_mode="HTML")
        await callback.answer()
        return

    challenger_balance = db.get_user_balance(challenger_id)
    opponent_balance = db.get_user_balance(opponent_id)

    if challenger_balance < amount or opponent_balance < amount:
        await callback.message.edit_text("Someone chickened out or went broke. The fight is off 💀.", parse_mode="HTML")
        await callback.answer("One of the fighters doesn't have enough points anymore!", show_alert=True)
        return

    winner_id, loser_id = random.choice([(challenger_id, opponent_id), (opponent_id, challenger_id)])
    
    db.update_user_balance(winner_id, amount)
    db.update_user_balance(loser_id, -amount)
    db.update_fight_stats(winner_id, loser_id)

    winner_info = db.get_user_info(winner_id)
    loser_info = db.get_user_info(loser_id)
    winner_name = get_display_name(winner_info[0], winner_info[1])
    loser_name = get_display_name(loser_info[0], loser_info[1])
    winner_new_balance = db.get_user_balance(winner_id)
    loser_new_balance = db.get_user_balance(loser_id)

    response_text = random.choice(FIGHT_WINNER).format(winner_name=escape_html(winner_name), loser_name=escape_html(loser_name), amount=amount, emoji=random.choice(WIN_EMOJI))
    
    final_response = (
        f"🥊 <b>THE DUEL IS OVER!</b>\n\n"
        f"{response_text}\n\n"
        f"<b>New Balances:</b>\n"
        f"📈 {escape_html(winner_name)}: <b>{winner_new_balance}</b> RP\n"
        f"📉 {escape_html(loser_name)}: <b>{loser_new_balance}</b> RP"
    )

    await callback.message.edit_text(final_response, parse_mode="HTML")
    await callback.answer()



@router.callback_query(F.data.startswith("gamble:again:"))
async def gamble_callback_handler(callback: CallbackQuery):
    _, _, user_id_str, amount_str = callback.data.split(':')
    user_id = int(user_id_str)
    amount = int(amount_str)

    if callback.from_user.id != user_id:
        await callback.answer("This is not your gamble lil bro!", show_alert=True)
        return

    is_cd, time_left, roast = db.get_cooldown_status(user_id, "gamble", 5)
    if is_cd:
        return await callback.answer(roast, show_alert=True)

    balance = db.get_user_balance(user_id)
    if balance < amount:
        await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, f"Bro is broke 💀. You don't have <b>{amount}</b> RP to try again.", inline_message_id=callback.inline_message_id)
        return await callback.answer("Not enough points.", show_alert=True)

    db.update_cooldown(user_id, "gamble")
    
    is_win, new_balance = run_gamble_logic(user_id, amount)

    if is_win:
        response_text = f"You locked in and won <b>{amount}</b> RP! W mans 🍷🗿."
    else:
        response_text = f"Oof! Fumbled the bag 💀. You lost <b>{amount}</b> RP."

    full_response = f"{response_text}\n\nYour new balance: <b>{new_balance}</b> RP."
    
    await edit_or_answer(
        callback.bot,
        callback.message.chat.id if callback.message else None,
        callback.message.message_id if callback.message else None,
        full_response,
        reply_markup=kb.create_gamble_keyboard(user_id, amount),
        inline_message_id=callback.inline_message_id
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("public_challenge:accept"))
async def public_challenge_callback_handler(callback: CallbackQuery):
    _, _, challenge_id_str = callback.data.split(':')
    challenge_id = int(challenge_id_str)
    
    challenge = db.get_public_challenge(challenge_id)
    if not challenge or challenge['status'] != 'active':
        await callback.answer("This challenge is no longer available. Too slow!", show_alert=True)
        return

    acceptor_user = callback.from_user
    if acceptor_user.id == challenge['challenger_id']:
        await callback.answer("You cannot accept your own challenge. Who are you fighting, your demons?", show_alert=True)
        return

    db.add_or_update_user(acceptor_user.id, acceptor_user.username, acceptor_user.full_name)
    acceptor_balance = db.get_user_balance(acceptor_user.id)
    if acceptor_balance < challenge['amount']:
        await callback.answer("You don't have enough Rizz Points to accept this challenge. Broke vibes.", show_alert=True)
        return

    db.accept_public_challenge(challenge_id, acceptor_user.id)

    challenger_id = challenge['challenger_id']
    amount = challenge['amount']

    challenger_info = db.get_user_info(challenger_id)
    acceptor_info = db.get_user_info(acceptor_user.id)
    challenger_name = get_display_name(challenger_info[0], challenger_info[1])
    acceptor_name = get_display_name(acceptor_info[0], acceptor_info[1])

    text = f"{escape_html(acceptor_name)} stepped up to the plate against {escape_html(challenger_name)}! The brawl for <b>{amount}</b> RP begins!"
    await edit_or_answer(callback.bot, callback.message.chat.id if callback.message else None, callback.message.message_id if callback.message else None, text, reply_markup=None, inline_message_id=callback.inline_message_id)

    winner_id, loser_id = random.choice([(challenger_id, acceptor_user.id), (acceptor_user.id, challenger_id)])
    
    db.update_user_balance(winner_id, amount)
    db.update_user_balance(loser_id, -amount)
    db.update_fight_stats(winner_id, loser_id)

    winner_info = db.get_user_info(winner_id)
    loser_info = db.get_user_info(loser_id)
    winner_name = get_display_name(winner_info[0], winner_info[1])
    loser_name = get_display_name(loser_info[0], loser_info[1])
    winner_new_balance = db.get_user_balance(winner_id)
    loser_new_balance = db.get_user_balance(loser_id)

    response_text = random.choice(FIGHT_WINNER).format(winner_name=escape_html(winner_name), loser_name=escape_html(loser_name), amount=amount, emoji=random.choice(WIN_EMOJI))
    
    final_response = (
        f"🥊 <b>THE DUEL IS OVER!</b>\n\n"
        f"{response_text}\n\n"
        f"<b>New Balances:</b>\n"
        f"📈 {escape_html(winner_name)}: <b>{winner_new_balance}</b> RP\n"
        f"📉 {escape_html(loser_name)}: <b>{loser_new_balance}</b> RP"
    )

    await callback.message.reply(final_response, parse_mode="HTML")
    db.delete_public_challenge(challenge_id)
    await callback.answer()

async def check_expired_loans(bot: Bot):
    expired_loans = db.get_expired_loans()
    for loan in expired_loans:
        user_id = loan['user_id']
        outstanding_balance = loan['outstanding_balance']
        user_balance = db.get_user_balance(user_id)

        if user_balance >= outstanding_balance:
            db.update_user_balance(user_id, -outstanding_balance)
            db.update_loan_status(loan['loan_id'], 'paid')
            try:
                await bot.send_message(user_id, f"The bank just forcefully collected. Your loan of {loan['loan_amount']} has been automatically paid off from your balance.", parse_mode="HTML")
            except Exception as e:
                pass
        else:
            if user_balance > 0:
                db.pay_loan(user_id, user_balance)
                new_outstanding = outstanding_balance - user_balance
                db.update_loan_status(loan['loan_id'], 'expired')
                try:
                    await bot.send_message(user_id, f"Your loan of {loan['loan_amount']} expired. The bank drained your <b>{user_balance}</b> RP but it wasn't enough. You still owe <b>{new_outstanding}</b> RP. 💀", parse_mode="HTML")
                except Exception as e:
                    pass
            else:
                db.update_loan_status(loan['loan_id'], 'expired')
                try:
                    await bot.send_message(user_id, f"Your loan of {loan['loan_amount']} expired and you have literally 0 points to pay it back. Bro is in crippling debt. 📉", parse_mode="HTML")
                except Exception as e:
                    pass