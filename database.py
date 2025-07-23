import time
import aiosqlite
from config import DB_PATH, ADMIN_USER_ID

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                date_added TEXT,
                is_active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS access_keys (
                key TEXT PRIMARY KEY,
                created_by INTEGER,
                created_date TEXT,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_date TEXT
            )
        """)
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, is_active) VALUES (?, ?, 1)",
                         (ADMIN_USER_ID, "AdminPrincipal"))
        await db.commit()

async def is_user_authorized(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_active FROM users WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result and result[0] == 1