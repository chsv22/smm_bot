from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards import (
    tariffs_new_kb, tariffs_standard_kb, tariffs_max_kb,
    tariffs_max_active_kb, upgrade_kb, main_menu_kb,
)
from config import (
    Plan,
    TARIFF_STANDARD_TEXT, TARIFF_MAX_TEXT,
    WELCOME_TEXT,
)

router = Router()


# ─── Тарифы ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu:tariffs")
async def show_tariffs(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    plan = user.get("plan", Plan.NONE) if user else Plan.NONE

    if plan == Plan.MAX:
        # Есть MAX — показываем его описание
        await callback.message.edit_text(
            TARIFF_MAX_TEXT + "\n\n✅ <b>Это ваш текущий тариф</b>",
            reply_markup=tariffs_max_active_kb(),
        )

    elif plan == Plan.STANDARD:
        # Есть Стандарт — показываем его описание + кнопка повысить
        await callback.message.edit_text(
            TARIFF_STANDARD_TEXT + "\n\n✅ <b>Это ваш текущий тариф</b>",
            reply_markup=tariffs_standard_kb(),
        )

    else:
        # Новый пользователь — показываем оба тарифа
        text = (
            TARIFF_STANDARD_TEXT
            + "\n" + "─" * 30 + "\n"
            + TARIFF_MAX_TEXT
        )
        await callback.message.edit_text(text, reply_markup=tariffs_new_kb())

    await callback.answer()


# ─── Повысить тариф ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "tariff:upgrade")
async def upgrade_tariff(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    plan = user.get("plan", Plan.NONE) if user else Plan.NONE

    if plan == Plan.MAX:
        # Уже MAX
        await callback.message.edit_text(
            "🎉 <b>Поздравляем!</b>\n\nУ вас уже максимальный тариф — <b>MAX</b>.\n"
            "Вы получаете лучшее из того, что мы предлагаем 💎",
            reply_markup=main_menu_kb(),
        )
    else:
        # Стандарт → предлагаем MAX
        await callback.message.edit_text(
            TARIFF_MAX_TEXT
            + "\n\n⬆️ <b>Хотите перейти на MAX?</b>\nНажмите кнопку ниже:",
            reply_markup=upgrade_kb(),
        )

    await callback.answer()


# ─── Подключить соцсети ───────────────────────────────────────────────────────

@router.callback_query(F.data == "tariff:connect")
async def tariff_connect(callback: CallbackQuery, state):
    from handlers.onboarding import cmd_connect
    await callback.answer()
    await cmd_connect(callback.message, state)


# ─── Новости ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu:news")
async def show_news(callback: CallbackQuery):
    from keyboards import news_kb
    await callback.message.edit_text(
        "📢 <b>Новости</b>\n\n"
        "Все актуальные новости, кейсы и обновления — в нашем Telegram-канале.\n\n"
        "Подписывайся, чтобы быть в курсе! 👇",
        reply_markup=news_kb(),
    )
    await callback.answer()
