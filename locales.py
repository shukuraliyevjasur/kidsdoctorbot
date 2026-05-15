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
        "change_language": "\U0001f310 Русский",
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
        "change_language": "\U0001f310 O'zbek",
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
