from aiogram import Router, types
from aiogram.filters import Command, CommandObject

import database as db
from handlers import get_target_user, get_display_name, escape_html

router = Router()

TRANSFER_FEE_PERCENT = 0.67 # Brutal 67% fee
MAX_DAILY_TRANSFERS = 5

@router.message(Command("transfer"))
async def transfer_handler(message: types.Message, command: CommandObject):
    """Handler for /transfer <@user> <amount>"""
    sender = message.from_user
    db.add_or_update_user(sender.id, sender.username, sender.full_name)

    if db.get_daily_transfer_count(sender.id) >= MAX_DAILY_TRANSFERS:
        await message.reply(f"You hit your daily limit of {MAX_DAILY_TRANSFERS} transfers. Chill out Mr. Beast.", parse_mode="HTML")
        return

    target = await get_target_user(message)
    if not target:
        await message.reply("Bro you need to specify a user to transfer to. Either mention them or reply to their message.", parse_mode="HTML")
        return
    
    if target.id == sender.id:
        await message.reply("Bro tried to send points to himself 💀. Infinite aura glitch denied.", parse_mode="HTML")
        return

    if not command.args:
        await message.reply("Incorrect format. Usage: <code>/transfer &lt;@user&gt; &lt;amount&gt;</code>", parse_mode="HTML")
        return
        
    args = command.args.split()
    amount_str = next((arg for arg in args if arg.isdigit()), None)

    if not amount_str:
        await message.reply("You must specify a valid amount to transfer.", parse_mode="HTML")
        return

    amount = int(amount_str)
    if amount <= 0:
        await message.reply("You can't transfer negative points, nice try buddy.", parse_mode="HTML")
        return

    fee = int(amount * TRANSFER_FEE_PERCENT)
    total_deduction = amount + fee
    
    sender_balance = db.get_user_balance(sender.id)
    if sender_balance < total_deduction:
        await message.reply(f"Bro is broke 💀. You need <b>{total_deduction}</b> RP (including a {fee} RP tax fee), but you only have <b>{sender_balance}</b>.", parse_mode="HTML")
        return

    db.add_or_update_user(target.id, target.username, target.full_name)
    db.transfer_points(sender.id, target.id, amount, fee)

    sender_name = get_display_name(sender.full_name, sender.username)
    target_name = get_display_name(target.full_name, target.username)

    await message.reply(
        f"💸 <b>Transfer Completed</b> 💸\n\n"
        f"{escape_html(sender_name)} just slid <b>{amount}</b> RP to {escape_html(target_name)}.\n\n"
        f"<i>Bro thought he could just slide Rizz around like it's nothing? The Rizz IRS intercepted a brutal <b>67% TAX</b> (<b>{fee}</b> RP) from the sender. Stay mad. 💀</i>",
        parse_mode="HTML"
    )