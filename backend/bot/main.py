"""
Telegram-бот: /start, приглашения в группу, callback голосования.
Запуск: python -m bot.main (из каталога backend)
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем backend в PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)
from sqlalchemy import select

from app.config import settings
from app.database import async_session, init_db
from app.models import Group, GroupMember, ProposalVote, User, VoteStatus
from app.notify import _send_message

logging.basicConfig(level=logging.INFO)
bot = Bot(token=settings.bot_token)
dp = Dispatcher()


def webapp_url() -> str:
    return settings.webapp_url.rstrip("/")


def webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Открыть календарь",
                    web_app=WebAppInfo(url=webapp_url()),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(maxsplit=1)
    start_param = args[1] if len(args) > 1 else None

    async with async_session() as db:
        result = await db.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "Пользователь",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        joined_group_name = None
        if start_param and start_param.startswith("group_"):
            code = start_param.replace("group_", "", 1)
            g_result = await db.execute(select(Group).where(Group.invite_code == code))
            group = g_result.scalar_one_or_none()
            if group:
                mem = await db.execute(
                    select(GroupMember).where(
                        GroupMember.group_id == group.id,
                        GroupMember.user_id == user.id,
                    )
                )
                if not mem.scalar_one_or_none():
                    db.add(GroupMember(group_id=group.id, user_id=user.id))
                    await db.commit()
                joined_group_name = group.name

    text = (
        "👋 <b>Meetup Planner</b> — планируйте встречи с друзьями.\n\n"
        "Откройте Mini App, выберите цвет, создайте группу и отмечайте "
        "свободные дни в общем календаре."
    )
    if joined_group_name:
        text += f"\n\n✅ Вы присоединились к группе «<b>{joined_group_name}</b>»."

    await message.answer(text, reply_markup=webapp_keyboard(), parse_mode="HTML")

    # Кнопка меню Web App
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(text="Календарь", web_app=WebAppInfo(url=webapp_url())),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("vote:"))
async def on_vote(callback: CallbackQuery):
    """Быстрый ответ Свободен/Занят из уведомления о предложении."""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ошибка данных")
        return

    _, proposal_id_str, status_str = parts
    proposal_id = int(proposal_id_str)
    status = VoteStatus.free if status_str == "free" else VoteStatus.busy

    async with async_session() as db:
        result = await db.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            await callback.answer("Сначала запустите /start")
            return

        from app.models import Proposal

        p_result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
        proposal = p_result.scalar_one_or_none()
        if not proposal:
            await callback.answer("Предложение не найдено")
            return

        existing = await db.execute(
            select(ProposalVote).where(
                ProposalVote.proposal_id == proposal_id,
                ProposalVote.user_id == user.id,
            )
        )
        vote = existing.scalar_one_or_none()
        if vote:
            vote.status = status
        else:
            db.add(ProposalVote(proposal_id=proposal_id, user_id=user.id, status=status))
        await db.commit()

    label = "свободны" if status == VoteStatus.free else "заняты"
    await callback.answer(f"Отмечено: вы {label}")
    await callback.message.edit_reply_markup(reply_markup=None)


async def setup_webapp_menu() -> None:
    """Глобальная кнопка меню с актуальным WEBAPP_URL (для всех чатов)."""
    url = settings.webapp_url.rstrip("/")
    if not url.startswith("https://"):
        logging.error(
            "WEBAPP_URL должен быть HTTPS (сейчас: %s). "
            "Задайте в Render: https://meetup-planner.onrender.com",
            settings.webapp_url,
        )
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Календарь",
                web_app=WebAppInfo(url=url),
            )
        )
        logging.info("Menu Web App URL: %s", url)
    except Exception as e:
        logging.warning("Не удалось обновить Menu Button: %s", e)


async def setup_webhook() -> None:
    """Продакшен: один webhook вместо polling (нет Conflict на Render)."""
    url = f"{webapp_url()}/webhook/telegram"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url, drop_pending_updates=True)
    logging.info("Webhook: %s", url)


async def run_bot_polling() -> None:
    """Локальная разработка: polling (сначала снимаем webhook)."""
    if not settings.bot_token:
        logging.error("BOT_TOKEN не задан")
        return
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_webapp_menu()
    await dp.start_polling(bot, drop_pending_updates=True)


async def run_bot_webhook_mode() -> None:
    """Render: только menu + регистрация webhook, без polling."""
    if not settings.bot_token:
        logging.error("BOT_TOKEN не задан")
        return
    await setup_webapp_menu()
    await setup_webhook()


async def main():
    await init_db()
    await run_bot_polling()


if __name__ == "__main__":
    asyncio.run(main())
