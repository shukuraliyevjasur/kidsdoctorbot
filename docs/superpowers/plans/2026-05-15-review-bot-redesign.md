# Review-Only Bot Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strip the KidsDoc Telegram bot down to a single-purpose review tool with a simplified one-step onboarding and RU/UZ language support only.

**Architecture:** Three files are fully rewritten (`locales.py`, `keyboards.py`, `handlers.py`); one file gets a minor tweak (`database.py`). All infrastructure files (`app.py`, `main.py`, `config.py`, `dashboard.py`) are untouched. No DB schema changes.

**Tech Stack:** Python 3.x, aiogram v3, aiosqlite, SQLite

---

## File Map

| File | Change |
|---|---|
| `locales.py` | Full rewrite — RU + UZ strings, review flow only |
| `keyboards.py` | Full rewrite — language select, welcome-back, department, rating |
| `handlers.py` | Full rewrite — OnboardingFSM + ReviewFSM, no menu |
| `database.py` | One-line tweak — `is_fully_registered()` checks `first_name` only |
| `tests/test_locales.py` | New — unit tests for `_()` helper |
| `tests/test_database.py` | New — unit tests for `is_fully_registered()` |

---

## Task 1: Clone Repo and Verify Environment

**Files:** none

- [ ] **Step 1: Clone the repo**

```powershell
cd "C:\Project JndA\kidsdoctorbot"
git clone https://github.com/alexcorpbuissn-eng/KidsDoc .
```

- [ ] **Step 2: Create a virtual environment and install dependencies**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest
```

- [ ] **Step 3: Verify the bot token is configured**

Create a `.env` file in the project root (copy from `.env.example` if present, or create manually):

```
BOT_TOKEN=your_telegram_bot_token_here
```

- [ ] **Step 4: Confirm the existing bot runs (baseline)**

```powershell
python main.py
```

Expected: Bot starts in polling mode, no errors. Stop with Ctrl+C.

- [ ] **Step 5: Commit baseline**

```powershell
git add .
git commit -m "chore: local setup baseline"
```

---

## Task 2: Rewrite locales.py

**Files:**
- Modify: `locales.py`
- Create: `tests/test_locales.py`

- [ ] **Step 1: Write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_locales.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_uz_key_returns_uz_string():
    from locales import _
    assert _("enter_name", "uz") == "Ismingizni kiriting:"

def test_ru_key_returns_ru_string():
    from locales import _
    assert _("enter_name", "ru") == "Введите ваше имя:"

def test_unknown_lang_falls_back_to_uz():
    from locales import _
    assert _("enter_name", "xx") == "Ismingizni kiriting:"

def test_unknown_key_returns_key_itself():
    from locales import _
    assert _("nonexistent_key", "uz") == "nonexistent_key"

def test_welcome_back_contains_placeholder():
    from locales import _
    result = _("welcome_back", "ru")
    assert "{name}" in result

def test_all_departments_present_in_both_langs():
    from locales import _
    departments = ["pediatrician", "dentist", "ent", "orthopedist", "allergist", "massage", "diagnostics"]
    for dept in departments:
        assert _("dept_" + dept, "uz") != "dept_" + dept, f"Missing UZ translation for {dept}"
        assert _("dept_" + dept, "ru") != "dept_" + dept, f"Missing RU translation for {dept}"
```

- [ ] **Step 2: Run to verify it fails**

```powershell
pytest tests/test_locales.py -v
```

Expected: ImportError or AssertionError — tests fail because locales.py still has old content.

- [ ] **Step 3: Rewrite locales.py**

Replace the entire contents of `locales.py` with:

```python
TRANSLATIONS = {
    "uz": {
        "welcome_new": "Tilni tanlang / Выберите язык:",
        "enter_name": "Ismingizni kiriting:",
        "welcome_back": "Xush kelibsiz, {name}!",
        "choose_department": "Qaysi bo'limni baholaysiz?",
        "choose_rating": "Bahoning yulduzlarini tanlang:",
        "enter_comment": "Izoh yozing:",
        "review_submitted": "Rahmat! Sizning bahoyingiz qabul qilindi. ✓",
        "leave_review": "Sharh qoldirish",
        "change_language": "🌐 Русский",
        "dept_pediatrician": "Pediatr",
        "dept_dentist": "Stomatolog",
        "dept_ent": "LOR",
        "dept_orthopedist": "Ortoped",
        "dept_allergist": "Allergolog",
        "dept_massage": "Massaj",
        "dept_diagnostics": "Diagnostika",
    },
    "ru": {
        "welcome_new": "Tilni tanlang / Выберите язык:",
        "enter_name": "Введите ваше имя:",
        "welcome_back": "Добро пожаловать, {name}!",
        "choose_department": "Какой отдел вы хотите оценить?",
        "choose_rating": "Выберите оценку звёздами:",
        "enter_comment": "Напишите комментарий:",
        "review_submitted": "Спасибо! Ваш отзыв принят. ✓",
        "leave_review": "Оставить отзыв",
        "change_language": "🌐 O'zbek",
        "dept_pediatrician": "Педиатр",
        "dept_dentist": "Стоматолог",
        "dept_ent": "ЛОР",
        "dept_orthopedist": "Ортопед",
        "dept_allergist": "Аллерголог",
        "dept_massage": "Массаж",
        "dept_diagnostics": "Диагностика",
    },
}

def _(key: str, lang: str = "uz") -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["uz"]).get(key, key)
```

- [ ] **Step 4: Run tests and verify they pass**

```powershell
pytest tests/test_locales.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add locales.py tests/__init__.py tests/test_locales.py
git commit -m "refactor: rewrite locales to RU/UZ review-flow only"
```

---

## Task 3: Rewrite keyboards.py

**Files:**
- Modify: `keyboards.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_keyboards.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_language_keyboard_has_two_buttons():
    from keyboards import language_keyboard
    kb = language_keyboard()
    all_buttons = [btn.text for row in kb.keyboard for btn in row]
    assert "🇷🇺 Русский" in all_buttons
    assert "🇺🇿 O'zbek" in all_buttons

def test_welcome_back_keyboard_has_review_and_lang_buttons():
    from keyboards import welcome_back_keyboard
    kb_uz = welcome_back_keyboard("uz")
    all_texts_uz = [btn.text for row in kb_uz.keyboard for btn in row]
    assert "Sharh qoldirish" in all_texts_uz
    assert "🌐 Русский" in all_texts_uz

    kb_ru = welcome_back_keyboard("ru")
    all_texts_ru = [btn.text for row in kb_ru.keyboard for btn in row]
    assert "Оставить отзыв" in all_texts_ru
    assert "🌐 O'zbek" in all_texts_ru

def test_department_keyboard_has_seven_buttons():
    from keyboards import department_keyboard
    kb = department_keyboard("uz")
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(all_buttons) == 7

def test_department_callback_data_format():
    from keyboards import department_keyboard
    kb = department_keyboard("uz")
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith("dept:")

def test_rating_keyboard_has_five_buttons():
    from keyboards import rating_keyboard
    kb = rating_keyboard()
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(all_buttons) == 5

def test_rating_callback_data_format():
    from keyboards import rating_keyboard
    kb = rating_keyboard()
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith("rating:")
            rating_val = int(btn.callback_data.split(":")[1])
            assert 1 <= rating_val <= 5
```

- [ ] **Step 2: Run to verify it fails**

```powershell
pytest tests/test_keyboards.py -v
```

Expected: Tests fail — old `keyboards.py` doesn't have the right structure.

- [ ] **Step 3: Rewrite keyboards.py**

Replace the entire contents of `keyboards.py` with:

```python
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from locales import _

DEPARTMENTS = [
    "pediatrician", "dentist", "ent",
    "orthopedist", "allergist", "massage", "diagnostics",
]

def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="🇷🇺 Русский"),
            KeyboardButton(text="🇺🇿 O'zbek"),
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
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("dept_" + dept, lang), callback_data=f"dept:{dept}")]
        for dept in DEPARTMENTS
    ])

def rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rating:{i}")
        for i in range(1, 6)
    ]])
```

- [ ] **Step 4: Run tests and verify they pass**

```powershell
pytest tests/test_keyboards.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add keyboards.py tests/test_keyboards.py
git commit -m "refactor: rewrite keyboards to review-flow only"
```

---

## Task 4: Tweak database.py

**Files:**
- Modify: `database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_database.py`:

```python
import sys, os, sqlite3, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def make_test_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE users (
            telegram_id INTEGER PRIMARY KEY,
            first_name TEXT DEFAULT '',
            surname TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE user_language (
            telegram_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'uz'
        )
    """)
    conn.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            rating INTEGER,
            comment TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def test_is_fully_registered_false_when_no_user(monkeypatch):
    import database
    conn = make_test_db()
    monkeypatch.setattr(database, "get_connection", lambda: conn)
    assert database.is_fully_registered(99999) is False

def test_is_fully_registered_true_when_first_name_set(monkeypatch):
    import database
    conn = make_test_db()
    conn.execute("INSERT INTO users (telegram_id, first_name, surname) VALUES (1, 'Jasur', '')")
    conn.commit()
    monkeypatch.setattr(database, "get_connection", lambda: conn)
    assert database.is_fully_registered(1) is True

def test_is_fully_registered_false_when_first_name_empty(monkeypatch):
    import database
    conn = make_test_db()
    conn.execute("INSERT INTO users (telegram_id, first_name, surname) VALUES (2, '', '')")
    conn.commit()
    monkeypatch.setattr(database, "get_connection", lambda: conn)
    assert database.is_fully_registered(2) is False
```

- [ ] **Step 2: Run to verify tests fail or error**

```powershell
pytest tests/test_database.py -v
```

Expected: Tests may pass or fail depending on current `is_fully_registered` implementation. Note what happens — if it currently requires surname, the test `test_is_fully_registered_true_when_first_name_set` will fail.

- [ ] **Step 3: Open database.py and locate is_fully_registered**

Find the function — it will look something like:

```python
def is_fully_registered(user_id):
    # checks both first_name and surname are non-empty
```

- [ ] **Step 4: Change is_fully_registered to check first_name only**

Find the line that checks surname and remove it, so the function only checks that `first_name` is non-empty. The result should be:

```python
def is_fully_registered(user_id):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT first_name FROM users WHERE telegram_id = ?", (user_id,)
    )
    row = cursor.fetchone()
    return bool(row and row[0].strip())
```

> Note: The exact implementation may differ slightly from existing code — match the surrounding style. The key change is: no surname check, only `first_name`.

- [ ] **Step 5: Run tests and verify they pass**

```powershell
pytest tests/test_database.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add database.py tests/test_database.py
git commit -m "fix: is_fully_registered checks first_name only, surname no longer required"
```

---

## Task 5: Rewrite handlers.py

**Files:**
- Modify: `handlers.py`

No unit tests here — aiogram handlers require a running bot context. Verification is done via manual smoke test in Task 6.

- [ ] **Step 1: Replace handlers.py entirely**

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database
from keyboards import language_keyboard, welcome_back_keyboard, department_keyboard, rating_keyboard
from locales import _

router = Router()

# --- FSM ---

class OnboardingFSM(StatesGroup):
    waiting_for_name = State()

class ReviewFSM(StatesGroup):
    waiting_for_department = State()
    waiting_for_rating = State()
    waiting_for_comment = State()

# --- Language button texts (fixed, language-independent) ---

LANG_BUTTONS = {
    "🇷🇺 Русский": "ru",
    "🇺🇿 O'zbek": "uz",
    "🌐 Русский": "ru",
    "🌐 O'zbek": "uz",
}

# --- /start ---

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if database.is_fully_registered(user_id):
        lang = database.get_user_language(user_id)
        name = database.get_user_info(user_id)[0]
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await message.answer(
            _("welcome_new", "uz"),
            reply_markup=language_keyboard(),
        )

# --- Language selection (new users) and language toggle (returning users) ---

@router.message(F.text.in_(list(LANG_BUTTONS.keys())))
async def handle_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = LANG_BUTTONS[message.text]
    database.set_user_language(user_id, lang)

    if database.is_fully_registered(user_id):
        name = database.get_user_info(user_id)[0]
        await message.answer(
            _("welcome_back", lang).format(name=name),
            reply_markup=welcome_back_keyboard(lang),
        )
    else:
        await state.set_state(OnboardingFSM.waiting_for_name)
        await message.answer(_("enter_name", lang))

# --- Name input (new users only) ---

@router.message(OnboardingFSM.waiting_for_name)
async def handle_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = database.get_user_language(user_id)
    name = message.text.strip() or message.from_user.first_name or "—"
    database.register_user(user_id, name, "")
    await state.clear()
    await _ask_department(message, lang)

# --- "Leave a review" button (returning users) ---

@router.message(F.text.in_([_("leave_review", "uz"), _("leave_review", "ru")]))
async def handle_leave_review(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = database.get_user_language(user_id)
    await _ask_department(message, lang)

# --- Shared: start the review flow ---

async def _ask_department(message: Message, lang: str):
    await message.answer(
        _("choose_department", lang),
        reply_markup=department_keyboard(lang),
    )

# --- Department selection ---

@router.callback_query(F.data.startswith("dept:"))
async def handle_department(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = database.get_user_language(user_id)
    dept = callback.data.split(":", 1)[1]
    await state.set_state(ReviewFSM.waiting_for_rating)
    await state.update_data(department=dept)
    await callback.message.answer(_("choose_rating", lang), reply_markup=rating_keyboard())
    await callback.answer()

# --- Star rating ---

@router.callback_query(ReviewFSM.waiting_for_rating, F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = database.get_user_language(user_id)
    rating = int(callback.data.split(":", 1)[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewFSM.waiting_for_comment)
    await callback.message.answer(_("enter_comment", lang))
    await callback.answer()

# --- Comment and submission ---

@router.message(ReviewFSM.waiting_for_comment)
async def handle_comment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = database.get_user_language(user_id)
    data = await state.get_data()
    database.save_review(user_id, data["department"], data["rating"], message.text)
    await state.clear()
    await message.answer(_("review_submitted", lang))
```

- [ ] **Step 2: Run the full test suite to make sure nothing is broken**

```powershell
pytest tests/ -v
```

Expected: All tests from Tasks 2, 3, 4 still PASS. (No handler tests — that's expected.)

- [ ] **Step 3: Commit**

```powershell
git add handlers.py
git commit -m "refactor: rewrite handlers to review-only flow with OnboardingFSM + ReviewFSM"
```

---

## Task 6: Manual Smoke Test

Run the bot locally and verify every path end-to-end.

- [ ] **Step 1: Start the bot**

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

- [ ] **Step 2: New user — UZ path**

In Telegram, open the bot and send `/start`. Verify:
- Language keyboard appears with `🇷🇺 Русский` and `🇺🇿 O'zbek`
- Press `🇺🇿 O'zbek` → bot asks for name in Uzbek
- Type any name (e.g. `Jasur`) → bot immediately shows department inline keyboard in Uzbek
- Press any department → bot shows star rating keyboard
- Press any star → bot asks for comment in Uzbek
- Type a comment → bot replies with Uzbek thank-you message

- [ ] **Step 3: Returning user — language toggle**

Send `/start` again. Verify:
- Bot shows welcome-back message with `[Sharh qoldirish]` and `[🌐 Русский]` buttons
- Press `[🌐 Русский]` → bot immediately shows welcome-back in Russian with `[Оставить отзыв]` and `[🌐 O'zbek]` buttons
- Press `[Оставить отзыв]` → department keyboard appears in Russian
- Complete a second review in Russian

- [ ] **Step 4: New user — RU path**

Using a different Telegram account (or clearing the DB), send `/start`, pick `🇷🇺 Русский`, enter only a surname or partial name, verify the bot accepts it and proceeds.

- [ ] **Step 5: Verify reviews appear in the dashboard**

```powershell
streamlit run dashboard.py
```

Open `http://localhost:8501` — confirm submitted reviews appear with correct service names and ratings.

- [ ] **Step 6: Final commit**

```powershell
git add .
git commit -m "feat: review-only bot — strip all non-review flows, RU/UZ, single name step"
```

---

## Spec Coverage Check

| Spec requirement | Covered by |
|---|---|
| Remove About, Services, Change name, main menu | Task 5 — handlers.py has none of these |
| Single name field, accept anything | Task 5 `handle_name` — stores raw text, no validation |
| Immediately start review after name | Task 5 — `handle_name` calls `_ask_department` directly |
| New user: language first, then name | Task 5 `cmd_start` + `handle_language` |
| Returning user: welcome-back with name | Task 5 `cmd_start` returning-user branch |
| Language toggle button on welcome-back | Task 3 `welcome_back_keyboard` + Task 5 `handle_language` |
| Toggle flips language, re-renders welcome | Task 5 `handle_language` — checks `is_fully_registered`, shows welcome-back |
| RU + UZ only, no English | Task 2 — TRANSLATIONS has only `uz` and `ru` keys |
| 7 departments | Task 3 `DEPARTMENTS` list + Task 2 `dept_*` keys |
| 1–5 star rating | Task 3 `rating_keyboard` |
| Free-text comment | Task 5 `handle_comment` |
| Review saved to DB | Task 5 `handle_comment` — calls `database.save_review` |
| `is_fully_registered` checks first_name only | Task 4 |
