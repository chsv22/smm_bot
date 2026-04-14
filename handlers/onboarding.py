"""
Onboarding after payment — bot asks for social media access one by one.

Flow:
  /connect  (or triggered after plan activation)
  → Instagram login
  → TikTok login
  → YouTube channel URL
  → VKontakte group URL
  → Telegram channel @username
  → Done summary
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from config import Plan

router = Router()


# ─── States ───────────────────────────────────────────────────────────────────

class ConnectState(StatesGroup):
    instagram  = State()
    tiktok     = State()
    youtube    = State()
    vkontakte  = State()
    telegram   = State()


# ─── Keyboards ────────────────────────────────────────────────────────────────

def skip_kb(step: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip:{step}"))
    return builder.as_markup()


def done_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить доступы", callback_data="connect:edit"))
    return builder.as_markup()


# ─── Step texts ───────────────────────────────────────────────────────────────

STEPS = {
    "instagram": {
        "emoji": "📸",
        "name": "Instagram",
        "text": (
            "📸 <b>Instagram</b>\n\n"
            "Отправьте логин вашего Instagram-аккаунта или бизнес-страницы.\n\n"
            "<i>Например: @mybrand или mybrand</i>\n\n"
            "Мы запросим доступ через Meta Business для публикации от вашего имени."
        ),
    },
    "tiktok": {
        "emoji": "🎵",
        "name": "TikTok",
        "text": (
            "🎵 <b>TikTok</b>\n\n"
            "Отправьте ссылку на ваш TikTok-аккаунт или @username.\n\n"
            "<i>Например: @mybrand или https://tiktok.com/@mybrand</i>"
        ),
    },
    "youtube": {
        "emoji": "▶️",
        "name": "YouTube",
        "text": (
            "▶️ <b>YouTube</b>\n\n"
            "Отправьте ссылку на ваш YouTube-канал.\n\n"
            "<i>Например: https://youtube.com/@mybrand или https://youtube.com/channel/UC...</i>"
        ),
    },
    "vkontakte": {
        "emoji": "💙",
        "name": "ВКонтакте",
        "text": (
            "💙 <b>ВКонтакте</b>\n\n"
            "Отправьте ссылку на вашу группу или публичную страницу ВКонтакте.\n\n"
            "<i>Например: https://vk.com/mybrand или @mybrand</i>"
        ),
    },
    "telegram": {
        "emoji": "✈️",
        "name": "Telegram",
        "text": (
            "✈️ <b>Telegram-канал</b>\n\n"
            "Отправьте @username вашего Telegram-канала.\n\n"
            "<i>Например: @mybrand</i>\n\n"
            "⚠️ Не забудьте добавить нашего бота <b>@SMM_SOVHOZMEDIA_BOT</b> "
            "в администраторы канала с правом публикации."
        ),
    },
}

STEP_ORDER = ["instagram", "tiktok", "youtube", "vkontakte", "telegram"]


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(Command("connect"))
@router.message(F.text == "🔗 Подключить соцсети")
async def cmd_connect(message: Message, state: FSMContext):
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
    )
    await state.update_data(user_id=user["id"], accounts={})
    await state.set_state(ConnectState.instagram)
    await message.answer(
        "🔗 <b>Подключение социальных сетей</b>\n\n"
        "Сейчас я попрошу вас предоставить доступ к каждой платформе по очереди.\n"
        "Любой шаг можно пропустить — добавите позже через меню.\n\n"
        "Начнём! 👇\n\n" + STEPS["instagram"]["text"],
        reply_markup=skip_kb("instagram"),
    )


# ─── Instagram ────────────────────────────────────────────────────────────────

@router.message(ConnectState.instagram)
async def step_instagram(message: Message, state: FSMContext):
    await _save_and_next(message, state, "instagram", message.text.strip())


@router.callback_query(ConnectState.instagram, F.data == "skip:instagram")
async def skip_instagram(callback: CallbackQuery, state: FSMContext):
    await _save_and_next(callback.message, state, "instagram", None, edit=True)
    await callback.answer()


# ─── TikTok ───────────────────────────────────────────────────────────────────

@router.message(ConnectState.tiktok)
async def step_tiktok(message: Message, state: FSMContext):
    await _save_and_next(message, state, "tiktok", message.text.strip())


@router.callback_query(ConnectState.tiktok, F.data == "skip:tiktok")
async def skip_tiktok(callback: CallbackQuery, state: FSMContext):
    await _save_and_next(callback.message, state, "tiktok", None, edit=True)
    await callback.answer()


# ─── YouTube ──────────────────────────────────────────────────────────────────

@router.message(ConnectState.youtube)
async def step_youtube(message: Message, state: FSMContext):
    await _save_and_next(message, state, "youtube", message.text.strip())


@router.callback_query(ConnectState.youtube, F.data == "skip:youtube")
async def skip_youtube(callback: CallbackQuery, state: FSMContext):
    await _save_and_next(callback.message, state, "youtube", None, edit=True)
    await callback.answer()


# ─── VKontakte ────────────────────────────────────────────────────────────────

@router.message(ConnectState.vkontakte)
async def step_vkontakte(message: Message, state: FSMContext):
    await _save_and_next(message, state, "vkontakte", message.text.strip())


@router.callback_query(ConnectState.vkontakte, F.data == "skip:vkontakte")
async def skip_vkontakte(callback: CallbackQuery, state: FSMContext):
    await _save_and_next(callback.message, state, "vkontakte", None, edit=True)
    await callback.answer()


# ─── Telegram ─────────────────────────────────────────────────────────────────

@router.message(ConnectState.telegram)
async def step_telegram(message: Message, state: FSMContext):
    await _save_and_next(message, state, "telegram", message.text.strip())


@router.callback_query(ConnectState.telegram, F.data == "skip:telegram")
async def skip_telegram(callback: CallbackQuery, state: FSMContext):
    await _save_and_next(callback.message, state, "telegram", None, edit=True)
    await callback.answer()


# ─── Core logic ───────────────────────────────────────────────────────────────

async def _save_and_next(
    message: Message,
    state: FSMContext,
    current: str,
    value: str | None,
    edit: bool = False,
):
    data = await state.get_data()
    accounts: dict = data.get("accounts", {})
    user_id: int = data["user_id"]

    if value:
        accounts[current] = value
    await state.update_data(accounts=accounts)

    # Save to DB immediately
    await db.save_social_account(user_id, current, value or "")

    # Find next step
    idx = STEP_ORDER.index(current)
    next_steps = STEP_ORDER[idx + 1:]

    if not next_steps:
        # All done
        await state.clear()
        await _show_summary(message, accounts, edit=edit)
        return

    next_step = next_steps[0]
    next_state = {
        "tiktok":    ConnectState.tiktok,
        "youtube":   ConnectState.youtube,
        "vkontakte": ConnectState.vkontakte,
        "telegram":  ConnectState.telegram,
    }[next_step]

    await state.set_state(next_state)

    step_num = STEP_ORDER.index(next_step) + 1
    progress = f"Шаг {step_num} из {len(STEP_ORDER)}\n\n"

    if edit:
        await message.edit_text(
            progress + STEPS[next_step]["text"],
            reply_markup=skip_kb(next_step),
        )
    else:
        await message.answer(
            progress + STEPS[next_step]["text"],
            reply_markup=skip_kb(next_step),
        )


async def _show_summary(message: Message, accounts: dict, edit: bool = False):
    lines = ["✅ <b>Социальные сети подключены!</b>\n"]
    for step in STEP_ORDER:
        info = STEPS[step]
        val = accounts.get(step)
        status = f"<code>{val}</code>" if val else "<i>не подключено</i>"
        lines.append(f"{info['emoji']} {info['name']}: {status}")

    lines.append(
        "\n\nНаша команда свяжется с вами в течение 24 часов для завершения настройки доступов."
    )

    text = "\n".join(lines)
    if edit:
        await message.edit_text(text, reply_markup=done_kb())
    else:
        await message.answer(text, reply_markup=done_kb())


# ─── Edit accounts ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "connect:edit")
async def connect_edit(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    accounts = await db.get_social_accounts(user["id"])
    await state.update_data(user_id=user["id"], accounts=accounts)
    await state.set_state(ConnectState.instagram)
    await callback.message.edit_text(
        "✏️ <b>Редактирование доступов</b>\n\n"
        "Шаг 1 из 5\n\n" + STEPS["instagram"]["text"],
        reply_markup=skip_kb("instagram"),
    )
    await callback.answer()
