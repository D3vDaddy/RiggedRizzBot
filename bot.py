import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram.types import BotCommand

from handlers import router, check_expired_loans
from games import router as games_router, draw_lottery_winner
from shop import router as shop_router
from transfer import router as transfer_router
from inline import router as inline_router
from admin import router as admin_router
import database as db


async def background_tasks(bot: Bot):
    """Run background tasks like checking for expired loans and bankrupt users."""
    while True:
        await check_expired_loans(bot)
        
        # Secret 3-Day Bankruptcy Forgiveness Check
        forgiven_users = db.check_and_forgive_bankruptcies()
        for uid in forgiven_users:
            try:
                await bot.send_message(
                    uid, 
                    "💀 <b>LIFELINE DEPLOYED</b> 💀\n\nBro was literally in the trenches for 3 straight days with negative aura. It was honestly pathetic to watch.\n\nThe Rizz Gods felt bad and forcefully reset your debt. You now have exactly <b>1 RP</b>. Don't fumble this second chance or you're eternally cooked.", 
                    parse_mode="HTML"
                )
            except Exception as e:
                pass
                
        await asyncio.sleep(3600)  # Check every hour

async def lottery_scheduler(bot: Bot):
    """Schedules the lottery to be drawn exactly 24h after the first ticket."""
    while True:
        await asyncio.sleep(60) # Check every 60 seconds
        if db.should_draw_lottery():
            await draw_lottery_winner(bot)

async def set_bot_commands(bot: Bot):
    """Registers bot commands in the Telegram UI menu."""
    commands = [
        BotCommand(command="start", description="Starts the bot"),
        BotCommand(command="help", description="Get help and see all commands"),
        BotCommand(command="rizz", description="View your Rizz Profile"),
        BotCommand(command="grow", description="Get your daily rizz bonus (or /daily)"),
        BotCommand(command="beg", description="Beg for some free RP (1h cooldown)"),
        BotCommand(command="leaderboard", description="See the top Rizz Kings"),
        BotCommand(command="shop", description="Buy items with your Rizz Points"),
        BotCommand(command="transfer", description="Send points to another user"),
        BotCommand(command="fight", description="Challenge a user to an aura duel"),
        BotCommand(command="loan", description="Take out a loan from the bank"),
        BotCommand(command="payloan", description="Pay back your bank debt"),
        BotCommand(command="slots", description="Play the slot machine"),
        BotCommand(command="blackjack", description="Play a game of Blackjack"),
        BotCommand(command="coinflip", description="Start or join a coinflip"),
        BotCommand(command="heist", description="Start a massive group heist"),
        BotCommand(command="join", description="Join an active heist or lobby"),
        BotCommand(command="gamble", description="Bet your points in a 50/50 game"),
        BotCommand(command="lottery", description="Buy a ticket for the daily draw"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Main function to start the bot."""
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the database
    db.init_db()
    db.populate_shop_if_empty()

    # Initialize bot and dispatcher
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("FATAL: TELEGRAM_BOT_TOKEN is not set in the .env file.")
        return

    # Using HTML ParseMode for cleaner formatting and to fix the newline bugs
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Include the command router
    dp.include_router(admin_router)
    dp.include_router(router)
    dp.include_router(games_router)
    dp.include_router(shop_router)
    dp.include_router(transfer_router)
    dp.include_router(inline_router)

    # Register commands in UI
    await set_bot_commands(bot)

    # Start background tasks
    asyncio.create_task(background_tasks(bot))
    asyncio.create_task(lottery_scheduler(bot))

    # Start polling
    logging.basicConfig(level=logging.INFO)
    print("Bot is starting and ready to mog...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)