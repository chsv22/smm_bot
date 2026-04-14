"""
Publishing handler — lets the user publish content to connected social networks.
Currently supports Instagram (photo + caption).
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


class PublishState(StatesGroup):
    choose_network = State()
    wait_photo     = State()
    wait_caption   = State()
    confirm        = State()


def publish_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📸 Instagram", callback_data="pub:instagram"))
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"))
    return builder.as_markup()


def confirm_publish_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Опубликовать", callback_data="pub:confirm"),
        InlineKeyboardButton(text="❌ Отмена",       callback_data="pub:cancel"),
    )
    return builder.as_markup()


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(Command("publish"))
@router.message(F.text == "📤 Опубликовать")
async def cmd_publish(message: Message, state: FSMContext):
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
    )
    if user.get("plan", Plan.NONE) == Plan.NONE:
        await message.answer("⚠️ Для публикации нужен активный тариф.")
        return

    accounts = await db.get_social_accounts(user["id"])
    if not accounts:
        await message.answer(
            "⚠️ Соцсети не подключены. Используйте /connect для подключения."
        )
        return

    await state.update_data(user_id=user["id"], accounts=accounts)
    await state.set_state(PublishState.choose_network)
    await message.answer(
        "📤 <b>Публикация</b>\n\nВыберите платформу:",
        reply_markup=publish_menu_kb(),
    )


# ─── Choose Instagram ─────────────────────────────────────────────────────────

@router.callback_query(PublishState.choose_network, F.data == "pub:instagram")
async def pub_choose_instagram(callback: CallbackQuery, state: FSMContext):
    await state.update_data(network="instagram")
    await state.set_state(PublishState.wait_photo)
    await callback.message.edit_text(
        "📸 <b>Публикация в Instagram</b>\n\n"
        "Отправьте фото которое хотите опубликовать.\n\n"
        "<i>Instagram требует изображение для поста</i>"
    )
    await callback.answer()


# ─── Receive photo ────────────────────────────────────────────────────────────

@router.message(PublishState.wait_photo, F.photo)
async def pub_receive_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(PublishState.wait_caption)
    await message.answer(
        "✍️ Теперь напишите подпись к посту (caption).\n\n"
        "Или отправьте <b>«-»</b> чтобы опубликовать без подписи."
    )


@router.message(PublishState.wait_photo)
async def pub_photo_wrong(message: Message):
    await message.answer("Пожалуйста, отправьте фото 📸")


# ─── Receive caption ──────────────────────────────────────────────────────────

@router.message(PublishState.wait_caption)
async def pub_receive_caption(message: Message, state: FSMContext):
    caption = "" if message.text == "-" else message.text.strip()
    await state.update_data(caption=caption)
    data = await state.get_data()

    await state.set_state(PublishState.confirm)
    preview_caption = caption or "<i>без подписи</i>"
    await message.answer_photo(
        data["photo_file_id"],
        caption=f"<b>Предпросмотр поста</b>\n\n{preview_caption}\n\n"
                f"Платформа: 📸 Instagram\n\nПубликуем?",
        reply_markup=confirm_publish_kb(),
    )


# ─── Confirm & publish ────────────────────────────────────────────────────────

@router.callback_query(PublishState.confirm, F.data == "pub:confirm")
async def pub_confirm(callback: CallbackQuery, state: FSMContext):
    from aiogram import Bot
    data = await state.get_data()
    await state.clear()

    wait_msg = await callback.message.answer("⏳ Публикую в Instagram...")
    await callback.answer()

    try:
        # Get public URL of the photo via Telegram Bot API
        bot: Bot = callback.bot
        file = await bot.get_file(data["photo_file_id"])
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

        from services.instagram import publish_photo
        result = await publish_photo(
            image_url=file_url,
            caption=data.get("caption", ""),
        )

        await wait_msg.delete()

        if result["success"]:
            await callback.message.answer(
                f"✅ <b>Опубликовано в Instagram!</b>\n\n"
                f"ID поста: <code>{result['post_id']}</code>\n\n"
                f"Пост появится в профиле @sovhozmedia"
            )
        else:
            await callback.message.answer(
                f"❌ Ошибка публикации:\n<code>{result['error']}</code>"
            )
    except Exception as e:
        await wait_msg.delete()
        await callback.message.answer(f"❌ Ошибка: {e}")


@router.callback_query(PublishState.confirm, F.data == "pub:cancel")
async def pub_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_caption(caption="❌ Публикация отменена.")
    await callback.answer()
