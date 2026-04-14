import aiosqlite
from datetime import datetime
from config import config, Plan

DB = config.database_path


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id   INTEGER UNIQUE NOT NULL,
                username      TEXT,
                full_name     TEXT,
                plan          TEXT DEFAULT 'none',
                registered_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS social_accounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                platform    TEXT NOT NULL,
                handle      TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                UNIQUE(user_id, platform),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.commit()


# ─── Users ────────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def create_user(telegram_id: int, username: str, full_name: str) -> dict:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, full_name, plan, registered_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, full_name, Plan.NONE, now),
        )
        await db.commit()
    return await get_user(telegram_id)


async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> dict:
    user = await get_user(telegram_id)
    if not user:
        user = await create_user(telegram_id, username, full_name)
    return user


async def set_plan(telegram_id: int, plan: str) -> None:
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET plan = ? WHERE telegram_id = ?", (plan, telegram_id)
        )
        await db.commit()


# ─── Social accounts ──────────────────────────────────────────────────────────

async def save_social_account(user_id: int, platform: str, handle: str) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """INSERT INTO social_accounts (user_id, platform, handle, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, platform) DO UPDATE SET handle=excluded.handle, updated_at=excluded.updated_at""",
            (user_id, platform, handle, now),
        )
        await db.commit()


async def get_social_accounts(user_id: int) -> dict:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT platform, handle FROM social_accounts WHERE user_id = ?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return {r["platform"]: r["handle"] for r in rows if r["handle"]}


# ─── Admin helpers ────────────────────────────────────────────────────────────

async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY registered_at DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE plan = ?", (Plan.STANDARD,)
        ) as cur:
            standard = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE plan = ?", (Plan.MAX,)
        ) as cur:
            max_plan = (await cur.fetchone())[0]
    return {"total": total, "standard": standard, "max": max_plan}
