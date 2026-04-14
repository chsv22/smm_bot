from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards import profile_kb
from config import Plan

router = Router()


@router.callback_query(F.data == "menu:profile")
async def show_profile(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    plan = user.get("plan", Plan.NONE) if user else Plan.NONE
    plan_name = Plan.NAMES.get(plan, "—")

    name = callback.from_user.full_name or callback.from_user.username or "—"
    username = f"@{callback.from_user.username}" if callback.from_user.username else "—"

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"Тариф: <b>{plan_name}</b>\n\n"
        f"Нажмите кнопку ниже, чтобы открыть мини-приложение:"
    )
    await callback.message.edit_text(text, reply_markup=profile_kb())
    await callback.answer()
