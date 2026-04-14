from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import (
    NEWS_CHANNEL_URL, PAYMENT_STANDARD, PAYMENT_MAX,
    MINI_APP_URL, Plan,
)


# ─── Главное меню ─────────────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль",  callback_data="menu:profile"))
    builder.row(InlineKeyboardButton(text="📢 Новости",  callback_data="menu:news"))
    builder.row(InlineKeyboardButton(text="💎 Тарифы",   callback_data="menu:tariffs"))
    return builder.as_markup()


# ─── Новости ──────────────────────────────────────────────────────────────────

def news_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Перейти в канал", url=NEWS_CHANNEL_URL))
    builder.row(InlineKeyboardButton(text="◀️ Главное меню",    callback_data="menu:main"))
    return builder.as_markup()


# ─── Тарифы — новый пользователь (нет тарифа) ────────────────────────────────

def tariffs_new_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 СТАНДАРТ", url=PAYMENT_STANDARD),
        InlineKeyboardButton(text="💎 MAX",       url=PAYMENT_MAX),
    )
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"))
    return builder.as_markup()


# ─── Тарифы — есть тариф «Стандарт» ──────────────────────────────────────────

def tariffs_standard_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬆️ Повысить тариф", callback_data="tariff:upgrade"))
    builder.row(InlineKeyboardButton(text="◀️ Главное меню",   callback_data="menu:main"))
    return builder.as_markup()


# ─── Тарифы — есть тариф «MAX» ───────────────────────────────────────────────

def tariffs_max_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"))
    return builder.as_markup()


# ─── Повысить тариф ───────────────────────────────────────────────────────────

def upgrade_kb() -> InlineKeyboardMarkup:
    """Shown when user is on Standard and wants to upgrade to MAX."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💎 Перейти к оплате MAX", url=PAYMENT_MAX))
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"))
    return builder.as_markup()


# ─── Профиль (мини-приложение) ────────────────────────────────────────────────

def profile_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="👤 Открыть профиль",
        web_app=__import__("aiogram.types", fromlist=["WebAppInfo"]).WebAppInfo(url=MINI_APP_URL),
    ))
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"))
    return builder.as_markup()
