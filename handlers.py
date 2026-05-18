import json
import logging
import traceback

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ErrorEvent
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database
from keyboards import language_keyboard, welcome_back_keyboard, department_keyboard, rating_keyboard
from locales import _

router = Router()

ST_WAITING_NAME    = "waiting_for_name"
ST_WAITING_RATING  = "waiting_for_rating"
ST_WAITING_COMMENT = "waiting_for_comment"

LANG_BUTTONS = {
    "\U0001f1f7\U0001f1fa Русский": "ru",
    "\U0001f1fa\U0001f1ff O'zbek":  "uz",
    "\U0001f310 Русский":           "ru",
    "\U0001f310 O'zbek":            "uz",
}


@router.error()
async def error_handler(event: ErrorEvent):
    logging.error(f"Aiogram handler error: {event.exception}\n{traceback.format_exc()}")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await database.clear_bot_state(user_id)
    logging.info(f"[start] user={user_id}")

    if await database.is_fully_registered(user_id):
        lang = await database.get_user_language(user_id)
        info = await database.get_user_info(user_id)
        name = info["first_name"] if info else message.from_user.first_name
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await message.answer(_("welcome_new", "uz"), reply_markup=language_keyboard())


@router.message(F.text.in_(list(LANG_BUTTONS.keys())))
async def handle_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = LANG_BUTTONS[message.text]
    logging.info(f"[language] user={user_id} lang={lang}")
    await database.set_user_language(user_id, lang)

    if await database.is_fully_registered(user_id):
        await database.clear_bot_state(user_id)
        info = await database.get_user_info(user_id)
        name = info["first_name"] if info else message.from_user.first_name
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await database.set_bot_state(user_id, ST_WAITING_NAME)
        await message.answer(_("enter_name", lang), reply_markup=ReplyKeyboardRemove())


@router.message(F.text.in_([_("leave_review", "uz"), _("leave_review", "ru")]))
async def handle_leave_review(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await database.get_user_language(user_id)
    logging.info(f"[leave_review] user={user_id}")
    await _ask_department(message, lang)


async def _ask_department(message: Message, lang: str):
    await message.answer(
        _("choose_department", lang),
        reply_markup=department_keyboard(lang),
    )


@router.callback_query(F.data.startswith("dept:"))
async def handle_department(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await database.get_user_language(user_id)
    dept = callback.data.split(":", 1)[1]
    logging.info(f"[dept] user={user_id} dept={dept}")
    await database.set_bot_state(user_id, ST_WAITING_RATING, json.dumps({"department": dept}))
    await callback.message.answer(_("choose_rating", lang), reply_markup=rating_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await database.get_user_language(user_id)
    bot_state = await database.get_bot_state(user_id)
    logging.info(f"[rating] user={user_id} bot_state={bot_state!r} data={callback.data}")
    if bot_state != ST_WAITING_RATING:
        logging.warning(f"[rating] unexpected state {bot_state!r} for user {user_id}")
        await callback.answer()
        return
    data = json.loads(await database.get_bot_state_data(user_id) or "{}")
    data["rating"] = int(callback.data.split(":", 1)[1])
    await database.set_bot_state(user_id, ST_WAITING_COMMENT, json.dumps(data))
    await callback.message.answer(_("enter_comment", lang))
    await callback.answer()


@router.message()
async def handle_text(message: Message, state: FSMContext):
    if not message.text:
        return
    user_id = message.from_user.id
    lang = await database.get_user_language(user_id)
    bot_state = await database.get_bot_state(user_id)
    logging.info(f"[text] user={user_id} bot_state={bot_state!r} text={message.text!r}")

    if bot_state == ST_WAITING_NAME or (
        not bot_state and not await database.is_fully_registered(user_id)
    ):
        name = message.text.strip() or message.from_user.first_name or "—"
        logging.info(f"[text] registering name={name!r} for user={user_id}")
        await database.register_user(user_id, message.from_user.username or "", name, "")
        await database.clear_bot_state(user_id)
        await _ask_department(message, lang)

    elif bot_state == ST_WAITING_COMMENT:
        data = json.loads(await database.get_bot_state_data(user_id) or "{}")
        logging.info(f"[text] saving comment for user={user_id} dept={data.get('department')}")
        await database.save_review(user_id, data.get("department", ""), data.get("rating", 0), message.text)
        await database.clear_bot_state(user_id)
        await message.answer(_("review_submitted", lang), reply_markup=welcome_back_keyboard(lang))
