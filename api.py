"""
FastAPI backend for SMM Bot Mini App.
Serves statistics aggregated from all connected social media platforms.
Also handles OAuth callbacks for VK and Instagram.
Run: uvicorn api:app --host 0.0.0.0 --port 8000
"""

import aiohttp
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import database as db
from config import config
from services.social_stats import get_aggregated_stats

app = FastAPI(title="SMM Bot Mini App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── Helper: send bot message ─────────────────────────────────────────────────

async def _bot_notify(telegram_id: int, text: str) -> None:
    """Send a message to a user via Telegram Bot API."""
    from aiogram import Bot
    bot = Bot(token=config.bot_token)
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML")
    finally:
        await bot.session.close()


# ─── OAuth: VK ────────────────────────────────────────────────────────────────

@app.get("/oauth/vk/callback", response_class=HTMLResponse)
async def vk_oauth_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    error_description: str = Query(default=""),
):
    """VK OAuth 2.0 redirect handler. state = telegram_id."""
    if error or not code:
        reason = error_description or error or "нет кода авторизации"
        return _oauth_page("ВКонтакте", success=False, reason=reason)

    try:
        telegram_id = int(state)
    except ValueError:
        return _oauth_page("ВКонтакте", success=False, reason="неверный параметр state")

    # Exchange code → access_token
    redirect_uri = f"{config.app_url}/oauth/vk/callback"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://oauth.vk.com/access_token",
            params={
                "client_id":     config.vk_app_id,
                "client_secret": config.vk_app_secret,
                "redirect_uri":  redirect_uri,
                "code":          code,
            },
        ) as r:
            data = await r.json()

    if "access_token" not in data:
        reason = data.get("error_description") or str(data)
        return _oauth_page("ВКонтакте", success=False, reason=reason)

    token   = data["access_token"]
    vk_uid  = str(data.get("user_id", ""))

    # Save to DB
    user = await db.get_user(telegram_id)
    if user:
        await db.save_oauth_token(user["id"], "vkontakte", vk_uid, token)

    await _bot_notify(telegram_id, "✅ <b>ВКонтакте подключён!</b>\n\nТеперь мы можем публиковать посты в вашем профиле.")
    return _oauth_page("ВКонтакте", success=True)


# ─── OAuth: Instagram (via Facebook/Meta) ─────────────────────────────────────

@app.get("/oauth/instagram/callback", response_class=HTMLResponse)
async def instagram_oauth_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    error_description: str = Query(default=""),
):
    """Meta/Instagram OAuth 2.0 redirect handler. state = telegram_id."""
    if error or not code:
        reason = error_description or error or "нет кода авторизации"
        return _oauth_page("Instagram", success=False, reason=reason)

    try:
        telegram_id = int(state)
    except ValueError:
        return _oauth_page("Instagram", success=False, reason="неверный параметр state")

    redirect_uri = f"{config.app_url}/oauth/instagram/callback"

    # Exchange code → short-lived user token
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id":     config.instagram_app_id,
                "client_secret": config.instagram_app_secret,
                "redirect_uri":  redirect_uri,
                "code":          code,
            },
        ) as r:
            token_data = await r.json()

    if "access_token" not in token_data:
        reason = token_data.get("error", {}).get("message") or str(token_data)
        return _oauth_page("Instagram", success=False, reason=reason)

    short_token = token_data["access_token"]

    # Exchange for long-lived token (60 days)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "grant_type":        "fb_exchange_token",
                "client_id":         config.instagram_app_id,
                "client_secret":     config.instagram_app_secret,
                "fb_exchange_token": short_token,
            },
        ) as r:
            ll_data = await r.json()

    long_token = ll_data.get("access_token", short_token)

    # Get Instagram business account ID
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://graph.facebook.com/v19.0/me",
            params={"fields": "id,name", "access_token": long_token},
        ) as r:
            me = await r.json()

    handle = me.get("name") or me.get("id") or ""

    user = await db.get_user(telegram_id)
    if user:
        await db.save_oauth_token(user["id"], "instagram", handle, long_token)

    await _bot_notify(
        telegram_id,
        f"✅ <b>Instagram подключён!</b>\n\nАккаунт: <b>{handle}</b>\n\nТеперь мы можем публиковать посты.",
    )
    return _oauth_page("Instagram", success=True)


# ─── OAuth result page ────────────────────────────────────────────────────────

def _oauth_page(platform: str, success: bool, reason: str = "") -> HTMLResponse:
    if success:
        body = f"""
        <div class="icon">✅</div>
        <h1>{platform} подключён!</h1>
        <p>Можете закрыть эту вкладку и вернуться в Telegram.</p>
        """
    else:
        body = f"""
        <div class="icon">❌</div>
        <h1>Ошибка подключения {platform}</h1>
        <p>{reason}</p>
        <p>Вернитесь в Telegram и попробуйте ещё раз.</p>
        """
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{platform} — {'Подключён' if success else 'Ошибка'}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f0f0f; color: #fff;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh; text-align: center; padding: 20px;
    }}
    .card {{ max-width: 400px; }}
    .icon {{ font-size: 72px; margin-bottom: 24px; }}
    h1 {{ font-size: 24px; margin-bottom: 12px; }}
    p {{ color: #aaa; line-height: 1.6; margin-top: 8px; }}
  </style>
</head>
<body><div class="card">{body}</div></body>
</html>"""
    return HTMLResponse(html)


# ─── Stats API ────────────────────────────────────────────────────────────────

@app.get("/api/stats/{telegram_id}")
async def stats(telegram_id: int, days: int = Query(default=30, ge=7, le=90)):
    user = await db.get_user(telegram_id)
    if not user:
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


# Serve Mini App HTML (must be last — catches all /app/* paths)
app.mount("/app", StaticFiles(directory="webapp", html=True), name="webapp")
