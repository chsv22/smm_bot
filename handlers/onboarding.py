"""
Onboarding after payment — bot sends OAuth links for each platform.

Flow:
  /connect  (or triggered after plan activation)
  → Bot shows inline URL-buttons for each platform
  → User clicks a button → browser opens OAuth page
  → After granting access, platform redirects to /oauth/{platform}/callback
  → Callback saves token to DB and sends bot confirmation
  → User returns to Telegram already connected
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from config import config, Plan

router = Router()


# ─── Keyboards ────────────────────────────────────────────────────────────────

def connect_kb(telegram_id: int) -> InlineKeyboardMarkup:
    """Build a keyboard with OAuth URL buttons for each platform."""
    builder = InlineKeyboardBuilder()

    app_url = config.app_url

    if config.vk_app_id:
        vk_scope = "wall,photos,video,docs,manage,offline"
        vk_url = (
            f"https://oauth.vk.com/authorize"
            f"?client_id={config.vk_app_id}"
            f"&redirect_uri={app_url}/oauth/vk/callback"
            f"&scope={vk_scope}"
            f"&response_type=code"
            f"&state={telegram_id}"
            f"&display=page"
        )
        builder.row(InlineKeyboardButton(text="💙 Подключить ВКонтакте", url=vk_url))

    if config.instagram_app_id:
        ig_scope = "instagram_basic,instagram_content_publish,pages_show_list,business_management"
        ig_url = (
            f"https://www.facebook.com/v19.0/dialog/oauth"
            f"?client_id={config.instagram_app_id}"
            f"&redirect_uri={app_url}/oauth/instagram/callback"
            f"&scope={ig_scope}"
            f"&response_type=code"
            f"&state={telegram_id}"
        )
        builder.row(InlineKeyboardButton(text="📸 Подключить Instagram", url=ig_url))

    # Platforms without OAuth automation yet — manual token entry
    builder.row(InlineKeyboardButton(text="🎵 TikTok",   callback_data="connect:tiktok"))
    builder.row(InlineKeyboardButton(text="▶️ YouTube",  callback_data="connect:youtube"))
    builder.row(InlineKeyboardButton(text="✈️ Telegram", callback_data="connect:telegram_ch"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"))
    return builder.as_markup()


def _status_icon(handle: str) -> str:
    return "✅" if handle else "⬜"


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(Command("connect"))
@router.message(F.text == "🔗 Подключить соцсети")
async def cmd_connect(message: Message):
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
    )
    if user.get("plan", Plan.NONE) == Plan.NONE:
        await message.answer("⚠️ Подключение соцсетей доступно после выбора тарифа.")
        return

    accounts = await db.get_social_accounts(user["id"])
    await message.answer(
        _connect_text(accounts),
        reply_markup=connect_kb(message.from_user.id),
    )


@router.callback_query(F.data == "connect:edit")
async def connect_edit(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    accounts = await db.get_social_accounts(user["id"]) if user else {}
    await callback.message.edit_text(
        _connect_text(accounts),
        reply_markup=connect_kb(callback.from_user.id),
    )
    await callback.answer()


def _connect_text(accounts: dict) -> str:
    lines = [
        "🔗 <b>Подключение социальных сетей</b>\n",
        "Нажмите кнопку платформы — откроется страница авторизации.",
        "После разрешения доступа вы получите подтверждение в боте.\n",
        f"{_status_icon(accounts.get('vkontakte', ''))} ВКонтакте",
        f"{_status_icon(accounts.get('instagram', ''))} Instagram",
        f"{_status_icon(accounts.get('tiktok', ''))} TikTok",
        f"{_status_icon(accounts.get('youtube', ''))} YouTube",
        f"{_status_icon(accounts.get('telegram', ''))} Telegram",
    ]
    return "\n".join(lines)


# ─── Manual text entry fallback (TikTok / YouTube / Telegram channel) ─────────

@router.callback_query(F.data == "connect:tiktok")
async def connect_tiktok(callback: CallbackQuery):
    await callback.message.answer(
        "🎵 <b>TikTok</b>\n\n"
        "Отправьте ваш TikTok @username или ссылку на профиль.\n\n"
        "<i>Например: @mybrand</i>"
    )
    await callback.answer()


@router.callback_query(F.data == "connect:youtube")
async def connect_youtube(callback: CallbackQuery):
    await callback.message.answer(
        "▶️ <b>YouTube</b>\n\n"
        "Отправьте ссылку на ваш YouTube-канал.\n\n"
        "<i>Например: https://youtube.com/@mybrand</i>"
    )
    await callback.answer()


@router.callback_query(F.data == "connect:telegram_ch")
async def connect_telegram_ch(callback: CallbackQuery):
    await callback.message.answer(
        "✈️ <b>Telegram-канал</b>\n\n"
        "Отправьте @username вашего Telegram-канала.\n\n"
        "⚠️ Добавьте бота <b>@SMM_SOVHOZMEDIA_BOT</b> в администраторы канала с правом публикации."
    )
    await callback.answer()
