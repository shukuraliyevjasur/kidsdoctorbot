import aiosqlite
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "clinic_bot.db")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # User Language for i18n
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_language (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uz'
            )
        ''')
        # Users Table (includes surname column)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                surname TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Reviews Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_name TEXT,
                rating INTEGER,
                review_text TEXT,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        # Bot state — replaces aiogram MemoryStorage (survives event-loop restarts)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bot_states (
                user_id INTEGER PRIMARY KEY,
                state   TEXT    NOT NULL DEFAULT '',
                data    TEXT    NOT NULL DEFAULT ''
            )
        ''')
        # Migration: add surname column to existing databases that lack it
        try:
            await db.execute('ALTER TABLE users ADD COLUMN surname TEXT')
        except Exception:
            pass  # Column already exists
        await db.commit()

async def get_user_language(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT language FROM user_language WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'uz'

async def set_user_language(user_id: int, language: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO user_language (user_id, language) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
        ''', (user_id, language))
        await db.commit()

async def user_exists(user_id: int) -> bool:
    """Check if a user has already completed registration."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def get_user_info(user_id: int) -> dict:
    """Fetch user's first_name and surname. Returns None if user doesn't exist."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT first_name, surname FROM users WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {'first_name': row[0], 'surname': row[1]}
            return None

async def is_fully_registered(user_id: int) -> bool:
    """Check if user has provided a name (first_name is non-empty)."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT first_name FROM users WHERE user_id = ? AND first_name IS NOT NULL AND first_name != ""',
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def register_user(user_id: int, username: str, first_name: str, surname: str = None):
    """Full registration — inserts new user or updates all fields."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (user_id, username, first_name, surname)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                username  = excluded.username,
                first_name = excluded.first_name,
                surname   = excluded.surname
        ''', (user_id, username, first_name, surname))
        await db.commit()

async def ensure_user_exists(user_id: int, username: str):
    """Safety net — creates a minimal record if none exists. Never overwrites names."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)
        ''', (user_id, username))
        await db.commit()

async def get_bot_state(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT state FROM bot_states WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ''

async def get_bot_state_data(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT data FROM bot_states WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ''

async def set_bot_state(user_id: int, state: str, data: str = ''):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO bot_states (user_id, state, data) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, data=excluded.data
        ''', (user_id, state, data))
        await db.commit()

async def clear_bot_state(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM bot_states WHERE user_id = ?', (user_id,))
        await db.commit()

async def save_review(user_id: int, service_name: str, rating: int, review_text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO reviews (user_id, service_name, rating, review_text) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, service_name, rating, review_text))
        await db.commit()
