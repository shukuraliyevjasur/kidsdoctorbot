# KidsDoc Bot — Review-Only Redesign

**Date:** 2026-05-15
**Scope:** Strip the bot down to a single-purpose review tool. Remove all non-review functionality. Simplify onboarding to one name step. Support RU/UZ only.

---

## What Gets Removed

- About clinic info handler
- Services info handler
- Change name handler
- English language (en) entirely
- Main menu keyboard (no menu at all)
- Multi-step name registration (first name then surname separately)

---

## User Flows

### New User

```
/start
  → Language selection keyboard: [🇷🇺 Русский] [🇺🇿 O'zbek]
  → "Enter your name:" (single free-text field — accept whatever is typed)
  → Department selection (inline keyboard, 7 options)
  → Star rating (inline keyboard, 1–5)
  → "Write your comment:" (free text)
  → "Thank you! Your review has been submitted. ✓"
```

### Returning User

```
/start
  → "Welcome back, [name]!" 
     + [Leave a review] button
     + [🌐 Русский / O'zbek] language toggle button (switches language in-place, no new prompt)
  → [Leave a review] pressed → Department selection
  → Star rating
  → "Write your comment:"
  → "Thank you! Your review has been submitted. ✓"
```

Language toggle on returning user screen: tapping it flips the saved language and re-renders the welcome screen in the new language immediately. No separate "pick language" step.

---

## Departments

Inline keyboard, one per row or 2-column grid:

1. Педиатр / Pediatr
2. Стоматолог / Stomatolog
3. ЛОР / LOR
4. Ортопед / Ortoped
5. Аллерголог / Allergolog
6. Массаж / Massaj
7. Диагностика / Diagnostika

---

## Languages

- Russian (ru) and Uzbek (uz) only
- Default for new users: Uzbek
- Stored in `user_language` table (existing schema, no change needed)
- Returning users keep their saved language until they toggle it

---

## FSM States

Two FSM groups:

**OnboardingFSM** (new users only):
- `waiting_for_name` — waiting for the user to type their name

**ReviewFSM** (all users):
- `waiting_for_department` — department inline keyboard shown (handled via callback)
- `waiting_for_rating` — star rating inline keyboard shown (handled via callback)
- `waiting_for_comment` — free text comment

No other FSM states needed.

---

## Database

No schema changes. Existing tables are sufficient:
- `user_language(telegram_id, language)` — language pref
- `users(telegram_id, first_name, surname)` — store the single name input in `first_name`, leave `surname` empty
- `reviews(id, user_id, service, rating, comment, timestamp)` — unchanged

`is_fully_registered()` logic: a user is registered if `first_name` is non-empty (surname no longer required).

---

## Files Changed

| File | Action |
|---|---|
| `handlers.py` | Full rewrite — new user flow + returning user flow + review FSM only |
| `keyboards.py` | Rewrite — language select, returning-user welcome, department, rating |
| `locales.py` | Rewrite — RU + UZ only, review-flow strings only |
| `database.py` | Minor tweak — `is_fully_registered()` checks first_name only |
| `app.py` | No change |
| `main.py` | No change |
| `config.py` | No change |
| `dashboard.py` | No change |

---

## Strings Needed (both languages)

- Welcome new user (no name yet)
- Language selected confirmation / prompt for name
- Enter your name prompt
- Welcome back greeting with name
- Choose department prompt
- Choose rating prompt
- Write comment prompt
- Review submitted confirmation
- Language toggle button label
- Leave a review button label
- All 7 department names
- Star labels (1★ through 5★)
