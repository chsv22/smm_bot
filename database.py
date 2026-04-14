import asyncpg
from datetime import datetime
from os import getenv
from config import Plan

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(getenv("DATABASE_URL"), min_size=1, max_size=5)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                telegram_id   BIGINT UNIQUE NOT NULL,
                username      TEXT DEFAULT '',
                full_name     TEXT DEFAULT '',
                plan          TEXT DEFAULT 'none',
                registered_at TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS social_accounts (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL,
                platform    TEXT NOT NULL,
                handle      TEXT NOT NULL DEFAULT '',
                token       TEXT NOT NULL DEFAULT '',
                updated_at  TEXT NOT NULL,
                UNIQUE(user_id, platform),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Migrate: add token column if not present (safe on existing tables)
        await conn.execute("""
            ALTER TABLE social_accounts ADD COLUMN IF NOT EXISTS token TEXT NOT NULL DEFAULT ''
        """)


# ─── Users ────────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1", telegram_id
        )
        return dict(row) if row else None


async def create_user(telegram_id: int, username: str, full_name: str) -> dict:
    now = datetime.utcnow().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (telegram_id, username, full_name, plan, registered_at)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (telegram_id) DO NOTHING""",
            telegram_id, username, full_name, Plan.NONE, now,
        )
    return await get_user(telegram_id)


async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> dict:
    user = await get_user(telegram_id)
    if not user:
        user = await create_user(telegram_id, username, full_name)
    return user


async def set_plan(telegram_id: int, plan: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET plan = $1 WHERE telegram_id = $2", plan, telegram_id
        )


# ─── Social accounts ──────────────────────────────────────────────────────────

async def save_social_account(user_id: int, platform: str, handle: str) -> None:
    now = datetime.utcnow().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO social_accounts (user_id, platform, handle, updated_at)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id, platform)
               DO UPDATE SET handle = EXCLUDED.handle, updated_at = EXCLUDED.updated_at""",
            user_id, platform, handle, now,
        )


async def save_oauth_token(user_id: int, platform: str, handle: str, token: str) -> None:
    """Save OAuth access token for a platform. Upserts on (user_id, platform)."""
    now = datetime.utcnow().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO social_accounts (user_id, platform, handle, token, updated_at)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (user_id, platform)
               DO UPDATE SET handle = EXCLUDED.handle,
                             token  = EXCLUDED.token,
                             updated_at = EXCLUDED.updated_at""",
            user_id, platform, handle, token, now,
        )


async def get_social_accounts(user_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT platform, handle FROM social_accounts WHERE user_id = $1", user_id
        )
        return {r["platform"]: r["handle"] for r in rows if r["handle"]}


# ─── Admin helpers ────────────────────────────────────────────────────────────

async def get_all_users() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY registered_at DESC")
        return [dict(r) for r in rows]


async def get_stats() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        total    = await conn.fetchval("SELECT COUNT(*) FROM users")
        standard = await conn.fetchval("SELECT COUNT(*) FROM users WHERE plan = $1", Plan.STANDARD)
        max_plan = await conn.fetchval("SELECT COUNT(*) FROM users WHERE plan = $1", Plan.MAX)
    return {"total": total, "standard": standard, "max": max_plan}
