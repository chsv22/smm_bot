from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from keyboards import main_menu_kb
from config import WELCOME_TEXT

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
    )
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_kb(),
    )


# Возврат в главное меню из любого раздела
@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
