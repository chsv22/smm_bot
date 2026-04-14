"""
FastAPI backend for SMM Bot Mini App.
Serves statistics aggregated from all connected social media platforms.
Run: uvicorn api:app --host 0.0.0.0 --port 8000
"""

import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import database as db
from services.social_stats import get_aggregated_stats

app = FastAPI(title="SMM Bot Mini App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Serve Mini App HTML
app.mount("/app", StaticFiles(directory="webapp", html=True), name="webapp")


@app.get("/api/stats/{telegram_id}")
async def stats(telegram_id: int, days: int = Query(default=30, ge=7, le=90)):
    """
    Return aggregated social media stats for a user.
    days — how many days of history to return for the reach chart.
    """
    user = await db.get_user(telegram_id)
    if not user:
        # Auto-create user if not exists (first open via mini app)
        user = await db.get_or_create_user(
            telegram_id=telegram_id,
            username="",
            full_name="Пользователь",
        )

    data = await get_aggregated_stats(telegram_id, days=days)
    return {"ok": True, "user": user, "stats": data}


@app.get("/health")
async def health():
    return {"status": "ok"}
