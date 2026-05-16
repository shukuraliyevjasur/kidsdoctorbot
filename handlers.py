from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database
from keyboards import language_keyboard, welcome_back_keyboard, department_keyboard, rating_keyboard
from locales import _

router = Router()


class OnboardingFSM(StatesGroup):
    waiting_for_name = State()


class ReviewFSM(StatesGroup):
    waiting_for_department = State()
    waiting_for_rating = State()
    waiting_for_comment = State()


# Maps every language button text → language code
LANG_BUTTONS = {
    "\U0001f1f7\U0001f1fa Русский": "ru",
    "\U0001f1fa\U0001f1ff O'zbek": "uz",
    "\U0001f310 Русский": "ru",
    "\U0001f310 O'zbek": "uz",
}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if await database.is_fully_registered(user_id):
        lang = await database.get_user_language(user_id)
        info = await database.get_user_info(user_id)
        name = info["first_name"] if info else message.from_user.first_name
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await message.answer(
            _("welcome_new", "uz"),
            reply_markup=language_keyboard(),
        )


@router.message(F.text.in_(list(LANG_BUTTONS.keys())))
async def handle_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = LANG_BUTTONS[message.text]
    await database.set_user_language(user_id, lang)

    if await database.is_fully_registered(user_id):
        info = await database.get_user_info(user_id)
        name = info["first_name"] if info else message.from_user.first_name
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await state.set_state(OnboardingFSM.waiting_for_name)
        await message.answer(_("enter_name", lang))


@router.message(OnboardingFSM.waiting_for_name)
async def handle_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await database.get_user_language(user_id)
    name = message.text.strip() or message.from_user.first_name or "—"
    username = message.from_user.username or ""
    await database.register_user(user_id, username, name, "")
    await state.clear()
    await _ask_department(message, lang)


@router.message(F.text.in_([_("leave_review", "uz"), _("leave_review", "ru")]))
async def handle_leave_review(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await database.get_user_language(user_id)
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
    await state.set_state(ReviewFSM.waiting_for_rating)
    await state.update_data(department=dept)
    await callback.message.answer(_("choose_rating", lang), reply_markup=rating_keyboard())
    await callback.answer()


@router.callback_query(ReviewFSM.waiting_for_rating, F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await database.get_user_language(user_id)
    rating = int(callback.data.split(":", 1)[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewFSM.waiting_for_comment)
    await callback.message.answer(_("enter_comment", lang))
    await callback.answer()


@router.message(ReviewFSM.waiting_for_comment)
async def handle_comment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await database.get_user_language(user_id)
    data = await state.get_data()
    await database.save_review(user_id, data["department"], data["rating"], message.text)
    await state.clear()
    await message.answer(_("review_submitted", lang))
