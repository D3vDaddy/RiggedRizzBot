# 👑 Rigged Rizz Bot

A highly engaging, async Telegram economy and casino bot built with Python and `aiogram` 3.x.

Designed for large group chats, this bot features a complete "Rizz" based economy packed with Gen-Z/brain-rot slang, multiplayer mini-games, a ruthless financial system, and a highly sophisticated anti-spam engine. It goes beyond simple balance tracking by offering paginated leaderboards, complex cooperative heists, and dynamic user titles based on server ranking.

## ✨ Core Features

(NOTE: ADMIN FEATURES ALSO ADDED TO LAZY TO EDIT README.md, figure it out yourself.)

### 📈 Dynamic Economy & Aura Levels

* **Rizz Points (RP):** The core currency. Users can check their `/balance` or view their detailed `/rizz` profile.
* **Dynamic Titles:** Ranks dynamically adapt based on the user's standing on the paginated `/leaderboard` (e.g., from *Supreme Sigma* down to *Cooked* or *NPC*).
* **Daily & Hourly Incomes:** Users can use `/grow` for daily claims (with potential item multipliers) and `/beg` for hourly pocket change.
* **Brutal IRS Tax:** Using `/transfer` to slide points to friends incurs a punishing 67% tax rate to prevent infinite money exploits.

### 🎲 Casino & Single-Player Games

* **`/blackjack`:** Fully functional Blackjack against a dealer with hit/stand mechanics and visible values.
* **`/slots`:** A 3-reel slot machine with multi-tier payouts (e.g., Triple Diamonds = 10x payout).
* **`/gamble` & `/coinflip`:** Fast-paced double-or-nothing games with easy "Play Again" inline buttons for seamless UX.
* **`/lottery`:** A global 24-hour drawing system that pools ticket purchases into a massive grand prize.

### ⚔️ Multiplayer & Co-op

* **`/fight`:** Users can challenge specific targets (or random NPCs) to winner-takes-all 1v1 PvP aura duels.
* **`/heist`:** A cooperative squad mission (Small or Big) requiring minimum player counts. Features complex RNG outcomes including *Flawless Victories*, *Total Busts*, and *Messy Getaways* (where half the crew escapes with the loot and the other half loses points).

### 🏦 Ruthless Financial System

* **Bank Loans:** Users can take out loans with 50% interest and a strict 7-day expiry `/loan` & `/payloan`.
* **Secret Bankruptcy Forgiveness:** A background async task constantly monitors users in deep debt. If a user maintains a negative balance for 3 consecutive days, the "Rizz Gods" secretly intervene, resetting their balance to exactly `1 RP` alongside a roasting DM.
* **Item Shop:** A built-in `/shop` where users can purchase persistent modifiers (e.g., permanent daily claim boosts).

### 🛡️ Advanced Dual-Logic Anti-Spam

Unlike standard rate limiters, this bot uses a custom SQLite-backed spam tracker that distinguishes between normal fast play and macro-spamming:

* **Free Play:** 0-second cooldowns on fast-paced games (slots, coinflip) for normal users.
* **Mashing Penalties:** Clicking inline buttons >3 times in under 1.5 seconds triggers an escalating lockout penalty and a custom roast message.
* **Global Spam Filter:** Sending 10 commands in 10 seconds triggers a hard 30-second global timeout across all endpoints.

## 🛠️ Technical Stack

* **Language:** Python 3.10+
* **Framework:** `aiogram` (v3.x)
* **Database:** `sqlite3` (Fully normalized schema with seamless on-the-fly migrations)
* **Asyncio:** Utilized for non-blocking UI interactions, background loan expirations, and lottery schedulers.

## 🚀 Installation & Setup

1. **Clone the repository:**

```bash
git clone https://github.com/D3vDaddy/RiggedRizzBot.git
cd RiggedRizzBot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Environment Setup:**
Create a .env file in the root directory and add your Telegram Bot Token:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

4. **Run the Bot:**
```bash
python bot.py
```

(The SQLite database rizz_economy.db will automatically initialize and configure its schema on the first run).
