from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Bot

import database as db
from config import config, Plan

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


# ─── Статистика ───────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_stats()
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: {stats['total']}\n"
        f"📦 Тариф «Стандарт»: {stats['standard']}\n"
        f"💎 Тариф «MAX»: {stats['max']}\n"
    )


# ─── Назначить тариф вручную ──────────────────────────────────────────────────

@router.message(Command("setplan"))
async def cmd_setplan(message: Message):
    """Usage: /setplan <telegram_id> <standard|max|none>"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3 or parts[2] not in (Plan.STANDARD, Plan.MAX, Plan.NONE):
        await message.answer(
            "Использование: /setplan <telegram_id> <standard|max|none>"
        )
        return
    tg_id = int(parts[1])
    plan = parts[2]
    user = await db.get_user(tg_id)
    if not user:
        await message.answer("Пользователь не найден.")
        return
    await db.set_plan(tg_id, plan)
    await message.answer(
        f"✅ Пользователю {tg_id} назначен тариф <b>{Plan.NAMES[plan]}</b>"
    )


# ─── Список пользователей ─────────────────────────────────────────────────────

@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        await message.answer("Пользователей нет.")
        return
    lines = [f"👥 <b>Пользователи</b> ({len(users)}):\n"]
    for u in users[:30]:
        name = u.get("full_name") or u.get("username") or str(u["telegram_id"])
        plan = Plan.NAMES.get(u.get("plan", Plan.NONE), "—")
        lines.append(f"• {name} | {u['telegram_id']} | {plan}")
    if len(users) > 30:
        lines.append(f"...и ещё {len(users) - 30}")
    await message.answer("\n".join(lines))


# ─── Рассылка ─────────────────────────────────────────────────────────────────

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot):
    """Usage: /broadcast <текст сообщения>"""
    if not is_admin(message.from_user.id):
        return
    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст>")
        return
    users = await db.get_all_users()
    sent, failed = 0, 0
    for u in users:
        try:
            await bot.send_message(u["telegram_id"], text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Отправлено: {sent}\n❌ Ошибок: {failed}")
