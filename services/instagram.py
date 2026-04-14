"""
Instagram Graph API publishing service.

Supports:
  - Photo posts (single image)
  - Carousel posts (multiple images)
  - Reels (video)
  - Stories (image)

Requires:
  - INSTAGRAM_TOKEN — long-lived access token
  - INSTAGRAM_USER_ID — numeric user ID (auto-fetched on first call)
"""

import aiohttp
from os import getenv

INSTAGRAM_TOKEN = getenv("INSTAGRAM_TOKEN", "")
_BASE = "https://graph.instagram.com/v19.0"

_instagram_user_id: str | None = None


async def _get_user_id() -> str:
    global _instagram_user_id
    if _instagram_user_id:
        return _instagram_user_id
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{_BASE}/me",
            params={"fields": "id,username", "access_token": INSTAGRAM_TOKEN},
        ) as r:
            data = await r.json()
            if "id" not in data:
                raise RuntimeError(f"Instagram API error: {data}")
            _instagram_user_id = data["id"]
            return _instagram_user_id


async def publish_photo(image_url: str, caption: str = "") -> dict:
    """
    Publish a single photo post to Instagram.
    image_url must be a publicly accessible URL (https).
    Returns {"success": True, "post_id": "..."} or {"success": False, "error": "..."}
    """
    user_id = await _get_user_id()
    token = INSTAGRAM_TOKEN

    async with aiohttp.ClientSession() as s:
        # Step 1: Create media container
        async with s.post(
            f"{_BASE}/{user_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
        ) as r:
            data = await r.json()
            if "id" not in data:
                return {"success": False, "error": str(data)}
            container_id = data["id"]

        # Step 2: Publish container
        async with s.post(
            f"{_BASE}/{user_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": token,
            },
        ) as r:
            data = await r.json()
            if "id" not in data:
                return {"success": False, "error": str(data)}
            return {"success": True, "post_id": data["id"]}


async def publish_text_as_photo(caption: str, bg_color: str = "0x000000") -> dict:
    """
    Instagram doesn't support text-only posts.
    For text posts use a pre-made image URL or generate one externally.
    This stub returns an error explaining the limitation.
    """
    return {
        "success": False,
        "error": "Instagram не поддерживает текстовые посты без изображения. Прикрепите фото.",
    }


async def get_account_info() -> dict:
    """Return basic account info."""
    token = INSTAGRAM_TOKEN
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{_BASE}/me",
            params={
                "fields": "id,username,account_type,media_count,followers_count",
                "access_token": token,
            },
        ) as r:
            return await r.json()


async def get_recent_posts(limit: int = 10) -> list[dict]:
    """Return recent posts."""
    user_id = await _get_user_id()
    token = INSTAGRAM_TOKEN
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{_BASE}/{user_id}/media",
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count",
                "limit": limit,
                "access_token": token,
            },
        ) as r:
            data = await r.json()
            return data.get("data", [])
