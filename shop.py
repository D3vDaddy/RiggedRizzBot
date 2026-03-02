from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from handlers import escape_html

router = Router()

@router.message(Command("shop"))
async def shop_handler(message: types.Message):
    """Displays the Rizz Shop."""
    db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    items = db.get_shop_items()
    if not items:
        await message.reply("The shop is currently empty. The owner is probably touching grass.")
        return

    shop_text = "🛒 <b>The Rizz Shop</b>\n\nSpend your hard-earned Rizz Points to boost your aura and stop being an NPC:\n"
    
    builder = InlineKeyboardBuilder()
    for item in items:
        shop_text += f"\n- <b>{item['name']}</b> - {item['price']} RP\n  <i>{escape_html(item['description'])}</i>\n"
        builder.button(text=f"Buy {item['name']}", callback_data=f"shop:buy:{item['item_id']}")
    
    builder.adjust(1) # Display buttons in a single column
    await message.reply(shop_text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("shop:buy:"))
async def buy_item_callback(callback: types.CallbackQuery):
    """Handles the purchase of a shop item."""
    _, _, item_id_str = callback.data.split(':')
    item_id = int(item_id_str)
    user = callback.from_user

    item = db.get_shop_item(item_id)

    if not item:
        await callback.answer("Item not found. Glitch in the matrix.", show_alert=True)
        return

    if db.user_has_item(user.id, item_id):
        await callback.answer(f"Bro you already own the '{item['name']}' item. Save your points.", show_alert=True)
        return

    balance = db.get_user_balance(user.id)
    if balance < item['price']:
        await callback.answer(f"Bro is broke 💀. You need {item['price']} RP but only have {balance}.", show_alert=True)
        return

    try:
        db.buy_shop_item(user.id, item_id, item['price'])
        await callback.answer(f"You successfully copped the {item['name']}! Your aura just leveled up.", show_alert=True)
        await callback.message.edit_text(f"You successfully purchased <b>{item['name']}</b> for {item['price']} RP! Absolute W.", parse_mode="HTML")
    except Exception as e:
        await callback.answer("An error occurred during purchase. 📉", show_alert=True)
        print(f"Error buying item: {e}")