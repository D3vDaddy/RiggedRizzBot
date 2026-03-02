# admin.py
from aiogram import Router, types, F
from aiogram.filters import Command, Filter
from config import ADMIN_IDS
import database as db
from utils import get_display_name, escape_html

router = Router()

# Custom filter to check for admin ID
class IsAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMIN_IDS

@router.message(IsAdmin(), Command("giverp"))
async def give_rp(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Reply to a user's message to give them RP.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("Usage: /giverp <amount>")
            return
        
        amount = int(args[1])
        target_user = message.reply_to_message.from_user
        
        # Ensure the target user is in the database
        db.add_or_update_user(target_user.id, target_user.username, target_user.full_name)
        
        db.update_user_balance(target_user.id, amount)
        
        # Fetch user info for the display name
        target_user_info = db.get_user_info(target_user.id)
        # The get_user_info might return None if the user is not found, though add_or_update should prevent this.
        if not target_user_info:
            await message.reply("Could not find the user information for the target.")
            return

        # Correctly unpack user info
        full_name, username = target_user_info
        target_display_name = get_display_name(full_name, username)
        
        await message.reply(f"Successfully gave {amount} RP to {escape_html(target_display_name)}.")

    except (ValueError, IndexError):
        await message.reply("Invalid amount. Usage: /giverp <amount>")
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

@router.message(IsAdmin(), Command("stats"))
async def bot_stats(message: types.Message):
    stats = db.get_bot_stats()
    total_users = stats.get("total_users", 0)
    total_rp = stats.get("total_rp", 0)

    stats_text = (
        f"🤖 **Bot Statistics** 🤖\n\n"
        f"👥 **Total Users:** {total_users}\n"
        f"✨ **Total Rizz Points in Circulation:** {total_rp}"
    )

    await message.reply(stats_text, parse_mode="HTML")
