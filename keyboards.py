from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
import database as db

def create_social_rizz_keyboard(initiator_id: int, target_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Accept ✅", callback_data=f"social_rizz:accept:{initiator_id}:{target_id}")
    builder.button(text="Decline ❌", callback_data=f"social_rizz:decline:{initiator_id}:{target_id}")
    builder.adjust(2)
    return builder.as_markup()

def create_fight_keyboard(challenger_id: int, opponent_id: int, amount: int) -> InlineKeyboardMarkup:
    action_id = db.create_action_data('fight', {'challenger_id': challenger_id, 'opponent_id': opponent_id, 'amount': amount})
    builder = InlineKeyboardBuilder()
    builder.button(text="Lock In! ⚔️", callback_data=f"action:{action_id}:accept")
    builder.button(text="Duck the fade 🏃💨", callback_data=f"action:{action_id}:decline")
    builder.adjust(2)
    return builder.as_markup()

def create_gamble_keyboard(user_id: int, amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Try your luck again! 🎲", callback_data=f"gamble:again:{user_id}:{amount}")
    return builder.as_markup()

def create_public_challenge_keyboard(challenge_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Accept Brawl! 🥊", callback_data=f"public_challenge:accept:{challenge_id}")
    return builder.as_markup()

def create_slots_keyboard(user_id: int, amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Spin Again! 🎰", callback_data=f"slots:play_again:{user_id}:{amount}")
    return builder.as_markup()

def create_blackjack_keyboard(game_id: str) -> InlineKeyboardMarkup:
    hit_action_id = db.create_action_data('blackjack', {'game_id': game_id, 'move': 'hit'})
    stand_action_id = db.create_action_data('blackjack', {'game_id': game_id, 'move': 'stand'})
    builder = InlineKeyboardBuilder()
    builder.button(text="Hit 🃏", callback_data=f"action:{hit_action_id}")
    builder.button(text="Stand ✋", callback_data=f"action:{stand_action_id}")
    builder.adjust(2)
    return builder.as_markup()

def create_coinflip_keyboard(game_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Join Coinflip 🪙", callback_data=f"coinflip:join:{game_id}")
    return builder.as_markup()

def create_heist_keyboard(game_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Squad Up! 💰", callback_data=f"heist:join:{game_id}")
    return builder.as_markup()

def create_leaderboard_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Creates a pagination keyboard for the leaderboard."""
    builder = InlineKeyboardBuilder()
    if current_page > 1:
        builder.button(text="⬅️ Previous", callback_data=f"leaderboard:page:{current_page - 1}")
    if current_page < total_pages:
        builder.button(text="Next ➡️", callback_data=f"leaderboard:page:{current_page + 1}")
    builder.adjust(2)
    return builder.as_markup()