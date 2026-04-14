"""
Social media statistics aggregator.

Each platform has:
  - get_<platform>_stats(user_id, days) -> PlatformStats

Real API calls are stubbed — replace the _fetch_* methods with actual HTTP calls
once you have the API credentials configured in .env.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

from config import config


# ─── Data models ──────────────────────────────────────────────────────────────

@dataclass
class DailyReach:
    date: str          # ISO format: 2026-04-01
    reach: int


@dataclass
class PlatformStats:
    platform: str      # youtube, instagram, tiktok, vkontakte, telegram
    connected: bool
    followers: int
    total_posts: int
    total_views: int
    total_likes: int
    reach_history: list[DailyReach] = field(default_factory=list)
    male_pct: Optional[float] = None    # 0–100
    female_pct: Optional[float] = None  # 0–100


@dataclass
class AggregatedStats:
    platforms: list[PlatformStats]
    total_posts: int
    total_views: int
    total_likes: int
    avg_male_pct: float
    avg_female_pct: float
    reach_chart: dict[str, list]   # {labels: [...], datasets: [{platform, data}]}


# ─── Mock data generator (replace with real API calls) ─────────────────────

def _mock_reach_history(days: int, base: int, volatility: float = 0.3) -> list[DailyReach]:
    """Generate plausible-looking reach curve for demo purposes."""
    history = []
    value = base
    today = date.today()
    for i in range(days, 0, -1):
        day = today - timedelta(days=i)
        delta = int(value * volatility * (random.random() - 0.4))
        value = max(10, value + delta)
        history.append(DailyReach(date=day.isoformat(), reach=value))
    return history


def _mock_platform(
    platform: str,
    days: int,
    followers_range: tuple[int, int] = (500, 50_000),
    posts_range: tuple[int, int] = (10, 300),
    views_mul: int = 5,
    male_range: tuple[float, float] = (30.0, 70.0),
) -> PlatformStats:
    followers = random.randint(*followers_range)
    total_posts = random.randint(*posts_range)
    total_views = total_posts * views_mul * random.randint(50, 500)
    total_likes = int(total_views * random.uniform(0.03, 0.15))
    male_pct = round(random.uniform(*male_range), 1)

    return PlatformStats(
        platform=platform,
        connected=True,
        followers=followers,
        total_posts=total_posts,
        total_views=total_views,
        total_likes=total_likes,
        reach_history=_mock_reach_history(days, base=followers // 10),
        male_pct=male_pct,
        female_pct=round(100 - male_pct, 1),
    )


# ─── Platform fetchers (stub → replace with real API) ──────────────────────

async def _fetch_youtube(user_id: int, days: int) -> PlatformStats:
    """
    Real implementation:
        GET https://www.googleapis.com/youtube/v3/channels
        GET https://youtubeanalytics.googleapis.com/v2/reports
        Requires: YOUTUBE_API_KEY + OAuth2 token per user
    """
    if not config.youtube_api_key:
        return _mock_platform("youtube", days, followers_range=(100, 80_000))

    # TODO: real YouTube Data API v3 call
    # headers = {"Authorization": f"Bearer {user_oauth_token}"}
    # async with aiohttp.ClientSession() as s:
    #     r = await s.get("https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true", headers=headers)
    #     data = await r.json()
    return _mock_platform("youtube", days, followers_range=(100, 80_000))


async def _fetch_instagram(user_id: int, days: int) -> PlatformStats:
    """
    Real implementation:
        Meta Graph API — requires Instagram Business account + access token
        GET https://graph.instagram.com/me/insights
    """
    if not config.instagram_token:
        return _mock_platform("instagram", days, followers_range=(200, 60_000))

    # TODO: real Instagram Graph API call
    return _mock_platform("instagram", days, followers_range=(200, 60_000))


async def _fetch_tiktok(user_id: int, days: int) -> PlatformStats:
    """
    Real implementation:
        TikTok Research API or TikTok for Business API
        GET https://open.tiktokapis.com/v2/research/user/info/
    """
    if not config.tiktok_token:
        return _mock_platform("tiktok", days, followers_range=(300, 100_000), male_range=(40.0, 55.0))

    # TODO: real TikTok API call
    return _mock_platform("tiktok", days, followers_range=(300, 100_000), male_range=(40.0, 55.0))


async def _fetch_vkontakte(user_id: int, days: int) -> PlatformStats:
    """
    Real implementation:
        VK API — groups.getById, stats.get
        GET https://api.vk.com/method/stats.get?access_token=...
    """
    if not config.vk_token:
        return _mock_platform("vkontakte", days, followers_range=(100, 30_000), male_range=(45.0, 65.0))

    # TODO: real VK API call
    return _mock_platform("vkontakte", days, followers_range=(100, 30_000), male_range=(45.0, 65.0))


async def _fetch_telegram(user_id: int, days: int) -> PlatformStats:
    """
    Real implementation:
        Telegram Bot API — getChatMemberCount
        For analytics: use @ControllerBot or TGStat API
    """
    return _mock_platform("telegram", days, followers_range=(50, 20_000), views_mul=3, male_range=(35.0, 60.0))


# ─── Aggregator ───────────────────────────────────────────────────────────────

async def get_aggregated_stats(user_id: int, days: int = 30) -> dict:
    """Fetch stats from all platforms, merge and return as dict."""

    import asyncio
    platforms: list[PlatformStats] = await asyncio.gather(
        _fetch_youtube(user_id, days),
        _fetch_instagram(user_id, days),
        _fetch_tiktok(user_id, days),
        _fetch_vkontakte(user_id, days),
        _fetch_telegram(user_id, days),
    )

    connected = [p for p in platforms if p.connected]

    # ── Totals ──
    total_posts = sum(p.total_posts for p in connected)
    total_views = sum(p.total_views for p in connected)
    total_likes = sum(p.total_likes for p in connected)

    # ── Gender average ──
    male_vals = [p.male_pct for p in connected if p.male_pct is not None]
    female_vals = [p.female_pct for p in connected if p.female_pct is not None]
    avg_male = round(sum(male_vals) / len(male_vals), 1) if male_vals else 50.0
    avg_female = round(100 - avg_male, 1)

    # ── Reach chart data ──
    # Build shared date labels (last `days` days)
    today = date.today()
    labels = [(today - timedelta(days=i)).isoformat() for i in range(days, 0, -1)]

    datasets = []
    for p in connected:
        reach_by_date = {r.date: r.reach for r in p.reach_history}
        datasets.append({
            "platform": p.platform,
            "data": [reach_by_date.get(d, 0) for d in labels],
        })

    reach_chart = {"labels": labels, "datasets": datasets}

    # ── Platform breakdown ──
    platform_list = []
    for p in connected:
        platform_list.append({
            "platform": p.platform,
            "followers": p.followers,
            "total_posts": p.total_posts,
            "total_views": p.total_views,
            "total_likes": p.total_likes,
            "male_pct": p.male_pct,
            "female_pct": p.female_pct,
        })

    return {
        "total_posts": total_posts,
        "total_views": total_views,
        "total_likes": total_likes,
        "avg_male_pct": avg_male,
        "avg_female_pct": avg_female,
        "reach_chart": reach_chart,
        "platforms": platform_list,
    }
