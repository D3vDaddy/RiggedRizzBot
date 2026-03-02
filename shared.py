# shared.py
import random
from aiogram import Bot

WIN_EMOJI = ["😎", "😂", "🎉", "🔥", "💯", "✨", "👑", "🍷🗿", "🤫🧏‍♂️"]
LOSE_EMOJI = ["😢", "😭", "👎", "🤡", "💀", "📉", "💔", "🍳"]

async def edit_or_answer(bot: Bot, chat_id: int, message_id: int, text: str, reply_markup=None, inline_message_id: str = None):
    if inline_message_id:
        await bot.edit_message_text(
            inline_message_id=inline_message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
