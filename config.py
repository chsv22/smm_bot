from dataclasses import dataclass, field
from os import getenv
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: getenv("BOT_TOKEN", ""))
    anthropic_api_key: str = field(default_factory=lambda: getenv("ANTHROPIC_API_KEY", ""))
    admin_ids: list[int] = field(default_factory=lambda: [
        int(x) for x in getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
    ])
    database_path: str = field(default_factory=lambda: getenv("DATABASE_PATH", "smm_bot.db"))

    # ── Social media API keys (optional — without them mock data is used) ──
    youtube_api_key: str   = field(default_factory=lambda: getenv("YOUTUBE_API_KEY", ""))
    instagram_token: str   = field(default_factory=lambda: getenv("INSTAGRAM_TOKEN", ""))
    tiktok_token: str      = field(default_factory=lambda: getenv("TIKTOK_TOKEN", ""))
    vk_token: str          = field(default_factory=lambda: getenv("VK_TOKEN", ""))

    # ── Mini App ──
    mini_app_host: str = field(default_factory=lambda: getenv("MINI_APP_HOST", "0.0.0.0"))
    mini_app_port: int = field(default_factory=lambda: int(getenv("MINI_APP_PORT", "8000")))


# ─── Links ────────────────────────────────────────────────────────────────────

NEWS_CHANNEL_URL    = "https://t.me/SMM_SOVHOZMEDIA"
PAYMENT_STANDARD    = "https://example.com/pay/standard"   # заглушка
PAYMENT_MAX         = "https://example.com/pay/max"        # заглушка
MINI_APP_URL        = getenv("MINI_APP_URL", "https://example.com/app")  # HTTPS обязателен для Telegram Mini App


# ─── Plans ────────────────────────────────────────────────────────────────────

class Plan:
    NONE     = "none"
    STANDARD = "standard"
    MAX      = "max"

    NAMES = {
        NONE:     "Нет тарифа",
        STANDARD: "Стандарт",
        MAX:      "MAX",
    }


# ─── Texts ────────────────────────────────────────────────────────────────────

WELCOME_TEXT = """
👋 <b>SMMщик в кармане</b>

Сервис для ведения социальных сетей, построенный полностью на базе ИИ.

Работаем 24/7 🔥

Мы помогаем бизнесам в SMM быстрее, дешевле и качественнее. Где нейросети пишут черновики и аналитику — мы дорабатываем это тактикой. Где «классика» тратит недели — мы делаем за часы.
"""

TARIFF_STANDARD_TEXT = """
📦 <b>Тариф «Стандарт»</b>

Ведение пакета социальных сетей:
• ВКонтакте
• TikTok
• Instagram
• YouTube
• Telegram

✅ Консультация по трендам в вашей нише
✅ Разработка уникального стиля и стратегии
✅ Генерация контента под ключ
✅ Каждый день публикуется <b>1 публикация</b> (пост/видео)
✅ Общая аналитика

<i>Подходит для создания портфолио, ведения блога</i>
"""

TARIFF_MAX_TEXT = """
💎 <b>Тариф «MAX»</b>

Ведение пакета социальных сетей:
• ВКонтакте
• TikTok
• Instagram
• YouTube
• Telegram

✅ Консультация по трендам в вашей нише
✅ Разработка уникального стиля и стратегии
✅ Генерация контента под ключ
✅ Каждый день публикуется <b>3 публикации</b> (пост/видео)
✅ Общая аналитика
✅ Возможность ведения блога на YouTube (обговаривается персонально)

<i>Подходит для активного привлечения новых клиентов</i>
"""

config = Config()
