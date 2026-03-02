import sqlite3
import random
from datetime import datetime, timedelta
import math
import json

DB_NAME = "rizz_economy.db"
GLOBAL_SPAM_TRACKER = {}

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # User table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                rizz_points INTEGER NOT NULL,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                last_daily TEXT,
                negative_since TEXT
            )
        """)
        # Cooldown table with spam tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TEXT NOT NULL,
                spam_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, command)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                loan_amount INTEGER NOT NULL,
                outstanding_balance INTEGER NOT NULL,
                interest_rate REAL NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public_challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER NOT NULL,
                challenge_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL,
                message_id INTEGER,
                chat_id INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                status TEXT NOT NULL,
                creator_id INTEGER NOT NULL,
                pot_amount INTEGER NOT NULL DEFAULT 0,
                start_time TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_players (
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (game_id, user_id),
                FOREIGN KEY (game_id) REFERENCES games(game_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                purchase_date TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                effect TEXT NOT NULL 
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_items (
                user_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                purchase_date TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (item_id) REFERENCES shop_items(item_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                fee INTEGER NOT NULL,
                transfer_date TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_data (
                action_id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Safe schema migrations
        try: cursor.execute("ALTER TABLE users ADD COLUMN wins INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN losses INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE command_cooldowns ADD COLUMN spam_count INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN negative_since TEXT")
        except sqlite3.OperationalError: pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blackjack_games (
                game_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                deck TEXT NOT NULL,
                player_hand TEXT NOT NULL,
                dealer_hand TEXT NOT NULL,
                bet_amount INTEGER NOT NULL,
                game_state TEXT NOT NULL
            )
        """)
        
        # Backfill negative_since for users who are already negative but missed the column addition
        cursor.execute("UPDATE users SET negative_since = ? WHERE rizz_points < 0 AND negative_since IS NULL", (datetime.now().isoformat(),))
        conn.commit()

def create_action_data(action_type: str, data: dict) -> str:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        action_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
        cursor.execute("INSERT INTO action_data (action_id, action_type, data) VALUES (?, ?, ?)", (action_id, action_type, json.dumps(data)))
        conn.commit()
        return action_id

def get_action_data(action_id: str) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT action_type, data FROM action_data WHERE action_id = ?", (action_id,))
        row = cursor.fetchone()
        if not row: return None
        return {"action_type": row[0], "data": json.loads(row[1])}

def create_blackjack_game(game_id: str, user_id: int, deck: str, player_hand: str, dealer_hand: str, bet_amount: int, game_state: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO blackjack_games (game_id, user_id, deck, player_hand, dealer_hand, bet_amount, game_state) VALUES (?, ?, ?, ?, ?, ?, ?)", (game_id, user_id, deck, player_hand, dealer_hand, bet_amount, game_state))
        conn.commit()

def get_blackjack_game(game_id: str) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blackjack_games WHERE game_id = ?", (game_id,))
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def update_blackjack_game(game_id: str, deck: str, player_hand: str, dealer_hand: str, game_state: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE blackjack_games SET deck = ?, player_hand = ?, dealer_hand = ?, game_state = ? WHERE game_id = ?", (deck, player_hand, dealer_hand, game_state, game_id))
        conn.commit()

def delete_blackjack_game(game_id: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blackjack_games WHERE game_id = ?", (game_id,))
        conn.commit()

def populate_shop_if_empty():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shop_items")
        if cursor.fetchone()[0] == 0:
            default_items = [
                ('Aura Booster', 'Locks in a +10% gamble win chance for 1 hour. Pure sigma energy.', 500, '{ "effect": "gamble_boost", "multiplier": 1.1, "duration": 3600 }'),
                ('Permanent Daily Aura', 'Permanently boosts your /grow daily by 50 RP. Passive income glitch.', 3000, '{ "effect": "permanent_daily_increase", "amount": 50 }'),
                ('Flex Title: \'The Honored One\'', 'A custom title to flex your aura level in /rizz.', 2500, '{ "effect": "title", "title": "The Honored One" }')
            ]
            cursor.executemany("INSERT INTO shop_items (name, description, price, effect) VALUES (?, ?, ?, ?)", default_items)
            conn.commit()

def add_or_update_user(user_id: int, username: str | None, full_name: str) -> bool:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO users (user_id, username, full_name, rizz_points) VALUES (?, ?, ?, ?)",
                (user_id, username, full_name, 100)
            )
            conn.commit()
            return True
        else:
            cursor.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (username, full_name, user_id)
            )
            conn.commit()
            return False

def get_user_balance(user_id: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rizz_points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

def update_user_balance(user_id: int, amount: int):
    """Updates a user's rizz_points balance and tracks if they go into negative debt."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rizz_points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if not result:
            return
            
        current_balance = result[0]
        new_balance = current_balance + amount
        
        if new_balance < 0 and current_balance >= 0:
            # User just became broke
            cursor.execute("UPDATE users SET rizz_points = ?, negative_since = ? WHERE user_id = ?", (new_balance, datetime.now().isoformat(), user_id))
        elif new_balance >= 0:
            # User is out of the trenches, clear the timer
            cursor.execute("UPDATE users SET rizz_points = ?, negative_since = NULL WHERE user_id = ?", (new_balance, user_id))
        else:
            # User is staying in debt or staying positive
            cursor.execute("UPDATE users SET rizz_points = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()

def check_and_forgive_bankruptcies() -> list[int]:
    """Finds users who have been negative for 3 days, sets balance to 1, returns list of user IDs to DM."""
    forgiven_ids = []
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now = datetime.now()
        three_days_ago = now - timedelta(days=3)
        
        cursor.execute("SELECT user_id FROM users WHERE rizz_points < 0 AND negative_since <= ?", (three_days_ago.isoformat(),))
        users = cursor.fetchall()
        
        for u in users:
            uid = u[0]
            cursor.execute("UPDATE users SET rizz_points = 1, negative_since = NULL WHERE user_id = ?", (uid,))
            forgiven_ids.append(uid)
            
        conn.commit()
    return forgiven_ids

def get_leaderboard_paginated(page: int, limit: int = 10) -> tuple[int, list]:
    """Returns (total_users, list_of_users_for_page)."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        offset = (page - 1) * limit
        cursor.execute("SELECT full_name, rizz_points FROM users ORDER BY rizz_points DESC LIMIT ? OFFSET ?", (limit, offset))
        return total_users, cursor.fetchall()

def get_leaderboard() -> list:
    """Legacy backward compatibility for quick grabs."""
    _, users = get_leaderboard_paginated(1, 10)
    return users

def get_daily_status(user_id: int) -> tuple[bool, int, int]:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            last_daily_time = datetime.fromisoformat(result[0])
            time_passed = datetime.now() - last_daily_time
            if time_passed < timedelta(hours=24):
                time_left = timedelta(hours=24) - time_passed
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return False, hours, minutes
        return True, 0, 0

def claim_daily(user_id: int, amount: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (now_iso, user_id))
        conn.commit()
    update_user_balance(user_id, amount)

def get_user_info(user_id: int) -> tuple | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, username FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def get_random_user(exclude_id: int) -> tuple | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, full_name FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (exclude_id,))
        return cursor.fetchone()

def update_fight_stats(winner_id: int, loser_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET wins = wins + 1 WHERE user_id = ?", (winner_id,))
        cursor.execute("UPDATE users SET losses = losses + 1 WHERE user_id = ?", (loser_id,))
        conn.commit()

def get_user_stats(user_id: int) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rizz_points, wins, losses FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if not result:
            return None
        return {"points": result[0], "wins": result[1], "losses": result[2]}

def get_user_rank(user_id: int) -> int | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users ORDER BY rizz_points DESC")
        leaderboard = cursor.fetchall()
        rank = next((i + 1 for i, (uid,) in enumerate(leaderboard) if uid == user_id), None)
        return rank

def take_loan(user_id: int, amount: int, interest_rate: float, duration_days: int) -> bool:
    if get_active_loan(user_id):
        return False
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=duration_days)
        outstanding_balance = amount + int(amount * interest_rate)
        cursor.execute(
            "INSERT INTO loans (user_id, loan_amount, outstanding_balance, interest_rate, issue_date, due_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, amount, outstanding_balance, interest_rate, issue_date.isoformat(), due_date.isoformat(), 'active')
        )
        conn.commit()
    update_user_balance(user_id, amount)
    return True

def get_active_loan(user_id: int) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans WHERE user_id = ? AND status = 'active'", (user_id,))
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def pay_loan(user_id: int, amount: int) -> str:
    active_loan = get_active_loan(user_id)
    if not active_loan: return "Bro you don't even have an active loan. W."

    payment = min(amount, active_loan['outstanding_balance'])
    new_balance = active_loan['outstanding_balance'] - payment

    update_user_balance(user_id, -payment)
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if new_balance <= 0:
            cursor.execute("UPDATE loans SET outstanding_balance = 0, status = 'paid' WHERE loan_id = ?", (active_loan['loan_id'],))
            conn.commit()
            return f"W mans! You fully paid off your loan. You paid <b>{payment}</b> RP to the bank."
        else:
            cursor.execute("UPDATE loans SET outstanding_balance = ? WHERE loan_id = ?", (new_balance, active_loan['loan_id']))
            conn.commit()
            return f"You paid <b>{payment}</b> RP towards your loan. You still owe <b>{new_balance}</b> RP."

def get_expired_loans() -> list[dict]:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("SELECT * FROM loans WHERE due_date < ? AND status = 'active'", (now_iso,))
        rows = cursor.fetchall()
        if not rows: return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

def update_loan_status(loan_id: int, status: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE loans SET status = ? WHERE loan_id = ?", (status, loan_id))
        conn.commit()

def create_public_challenge(challenger_id: int, challenge_type: str, amount: int, message_id: int, chat_id: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO public_challenges (challenger_id, challenge_type, amount, status, message_id, chat_id) VALUES (?, ?, ?, ?, ?, ?)",
            (challenger_id, challenge_type, amount, 'active', message_id, chat_id)
        )
        conn.commit()
        return cursor.lastrowid

def get_public_challenge(challenge_id: int) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM public_challenges WHERE challenge_id = ?", (challenge_id,))
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def accept_public_challenge(challenge_id: int, acceptor_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE public_challenges SET status = 'accepted' WHERE challenge_id = ?", (challenge_id,))
        conn.commit()

def delete_public_challenge(challenge_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM public_challenges WHERE challenge_id = ?", (challenge_id,))
        conn.commit()

def get_cooldown_status(user_id: int, command: str, base_cooldown_seconds: int) -> tuple[bool, int, str]:
    global GLOBAL_SPAM_TRACKER
    now = datetime.now()
    
    if user_id not in GLOBAL_SPAM_TRACKER:
        GLOBAL_SPAM_TRACKER[user_id] = []
        
    GLOBAL_SPAM_TRACKER[user_id] = [t for t in GLOBAL_SPAM_TRACKER[user_id] if (now - t).total_seconds() < 10]
    GLOBAL_SPAM_TRACKER[user_id].append(now)
    
    if len(GLOBAL_SPAM_TRACKER[user_id]) >= 10:
        return True, 30, "Bro go touch grass 🌿. You're spamming way too much! Wait 30 seconds."

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_used, spam_count FROM command_cooldowns WHERE user_id = ? AND command = ?", (user_id, command))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return False, 0, ""
            
        last_used_time = datetime.fromisoformat(result[0])
        spam_count = result[1] if result[1] is not None else 0
        time_since_last = (now - last_used_time).total_seconds()
        
        if base_cooldown_seconds > 10:
            if time_since_last < base_cooldown_seconds:
                time_left = int(base_cooldown_seconds - time_since_last)
                return True, time_left, f"Chill bro, you gotta wait <b>{time_left}s</b> before using /{command} again."
            else:
                return False, 0, ""

        SPAM_WINDOW, SPAM_LIMIT, PENALTY_TIME = 1.5, 3, 15

        if spam_count >= SPAM_LIMIT:
            if time_since_last < PENALTY_TIME:
                time_left = int(PENALTY_TIME - time_since_last)
                cursor.execute("UPDATE command_cooldowns SET last_used = ? WHERE user_id = ? AND command = ?", (now.isoformat(), user_id, command))
                conn.commit()
                roasts = [
                    f"Bro is spamming so hard the matrix broke 💀. You are locked out for <b>{time_left}s</b>.",
                    f"Negative aura behavior detected. Stop mashing! Touch grass for <b>{time_left}s</b>.",
                ]
                return True, time_left, random.choice(roasts)
            else:
                cursor.execute("UPDATE command_cooldowns SET spam_count = 0 WHERE user_id = ? AND command = ?", (user_id, command))
                conn.commit()
                return False, 0, ""

        if time_since_last < SPAM_WINDOW:
            new_spam_count = spam_count + 1
            if new_spam_count >= SPAM_LIMIT:
                cursor.execute("UPDATE command_cooldowns SET spam_count = ?, last_used = ? WHERE user_id = ? AND command = ?", (new_spam_count, now.isoformat(), user_id, command))
                conn.commit()
                return True, PENALTY_TIME, "Bro go touch grass 🌿. You are locked out for 15s for mashing."
            else:
                cursor.execute("UPDATE command_cooldowns SET spam_count = ? WHERE user_id = ? AND command = ?", (new_spam_count, user_id, command))
                conn.commit()
                return False, 0, ""
        else:
            if spam_count > 0:
                cursor.execute("UPDATE command_cooldowns SET spam_count = 0 WHERE user_id = ? AND command = ?", (user_id, command))
                conn.commit()
            return False, 0, ""

def update_cooldown(user_id: int, command: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("SELECT spam_count FROM command_cooldowns WHERE user_id = ? AND command = ?", (user_id, command))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE command_cooldowns SET last_used = ? WHERE user_id = ? AND command = ?", (now_iso, user_id, command))
        else:
            cursor.execute("INSERT INTO command_cooldowns (user_id, command, last_used, spam_count) VALUES (?, ?, ?, 0)", (user_id, command, now_iso))
        conn.commit()

# --- Game Functions ---
def create_game(game_type: str, creator_id: int, pot_amount: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        start_time = datetime.now().isoformat()
        cursor.execute("INSERT INTO games (game_type, status, creator_id, pot_amount, start_time) VALUES (?, ?, ?, ?, ?)", (game_type, 'waiting', creator_id, pot_amount, start_time))
        game_id = cursor.lastrowid
        cursor.execute("INSERT INTO game_players (game_id, user_id) VALUES (?, ?)", (game_id, creator_id))
        conn.commit()
        return game_id

def get_game(game_id: int) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def update_game_status(game_id: int, status: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE games SET status = ? WHERE game_id = ?", (status, game_id))
        conn.commit()

def add_player_to_game(game_id: int, user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO game_players (game_id, user_id) VALUES (?, ?)", (game_id, user_id))
        conn.commit()

def get_game_players(game_id: int) -> list:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM game_players WHERE game_id = ?", (game_id,))
        return [row[0] for row in cursor.fetchall()]

def lock_points(user_id: int, amount: int):
    update_user_balance(user_id, -amount)

def get_open_coinflip_game() -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games WHERE game_type = 'coinflip' AND status = 'waiting' ORDER BY start_time DESC LIMIT 1")
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def get_open_heist_game() -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games WHERE game_type LIKE 'heist%' AND status = 'waiting' ORDER BY start_time DESC LIMIT 1")
        row = cursor.fetchone()
        if not row: return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

# --- Lottery Functions ---
def buy_lottery_ticket(user_id: int, chat_id: int, price: int):
    update_user_balance(user_id, -price)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        purchase_date = datetime.now().isoformat()
        cursor.execute("INSERT INTO lottery_tickets (user_id, chat_id, purchase_date) VALUES (?, ?, ?)", (user_id, chat_id, purchase_date))
        conn.commit()

def get_time_until_lottery() -> tuple[int, int] | None:
    """Returns (hours, minutes) until the next draw, or None if no tickets exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(purchase_date) FROM lottery_tickets")
        result = cursor.fetchone()
        if not result or not result[0]:
            return None
            
        oldest_ticket_time = datetime.fromisoformat(result[0])
        time_passed = datetime.now() - oldest_ticket_time
        time_left = timedelta(hours=24) - time_passed
        
        if time_left.total_seconds() <= 0:
            return (0, 0)
            
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return (hours, minutes)

def should_draw_lottery() -> bool:
    """Checks if the oldest ticket is > 24 hours old."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(purchase_date) FROM lottery_tickets")
        result = cursor.fetchone()
        if not result or not result[0]:
            return False
            
        oldest_ticket_time = datetime.fromisoformat(result[0])
        if datetime.now() - oldest_ticket_time >= timedelta(hours=24):
            return True
        return False

def get_all_lottery_tickets() -> list[tuple[int, int]]:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, chat_id FROM lottery_tickets")
        return cursor.fetchall()

def clear_lottery_tickets():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lottery_tickets")
        conn.commit()

# --- Shop & Transfer ---
def get_shop_items() -> list:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shop_items")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_shop_item(item_id: int) -> dict | None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shop_items WHERE item_id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

def buy_shop_item(user_id: int, item_id: int, price: int):
    update_user_balance(user_id, -price)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        purchase_date = datetime.now().isoformat()
        cursor.execute("INSERT INTO user_items (user_id, item_id, purchase_date) VALUES (?, ?, ?)", (user_id, item_id, purchase_date))
        conn.commit()

def get_user_items(user_id: int) -> list:
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT si.* FROM user_items ui JOIN shop_items si ON ui.item_id = si.item_id WHERE ui.user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def user_has_item(user_id: int, item_id: int) -> bool:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        return cursor.fetchone() is not None

def transfer_points(sender_id: int, receiver_id: int, amount: int, fee: int):
    update_user_balance(sender_id, -(amount + fee))
    update_user_balance(receiver_id, amount)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("INSERT INTO transfers (sender_id, receiver_id, amount, fee, transfer_date) VALUES (?, ?, ?, ?, ?)", (sender_id, receiver_id, amount, fee, now_iso))
        conn.commit()

def get_daily_transfer_count(user_id: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cursor.execute("SELECT COUNT(*) FROM transfers WHERE sender_id = ? AND transfer_date >= ?", (user_id, today_start))
        return cursor.fetchone()[0]

def get_bot_stats() -> dict:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(user_id), SUM(rizz_points) FROM users")
        total_users, total_rp = cursor.fetchone()
        return {"total_users": total_users, "total_rp": total_rp}