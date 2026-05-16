from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from locales import _

DEPARTMENTS = [
    "pediatrician", "neurology",
    "orthopedist",  "ent",
    "dentist",      "immunology",
    "gynecology",   "massage",
    "laboratory",   "neurosonography",
    "uzi",          "procedure",
    "allergist",    "diagnostics",
]


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="\U0001f1f7\U0001f1fa Русский"),
            KeyboardButton(text="\U0001f1fa\U0001f1ff O'zbek"),
        ]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def welcome_back_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("leave_review", lang))],
            [KeyboardButton(text=_("change_language", lang))],
        ],
        resize_keyboard=True,
    )


def department_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=_("dept_" + dept, lang), callback_data=f"dept:{dept}")
        for dept in DEPARTMENTS
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rating:{i}")
        for i in range(1, 6)
    ]])
