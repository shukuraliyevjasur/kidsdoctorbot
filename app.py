"""
Unified Flask + aiogram Webhook application for Kids Doctor Clinic.
Merges the dashboard (Flask) and the Telegram bot (aiogram v3) into a single
WSGI-compatible app that runs on PythonAnywhere's free tier.

Dashboard:  GET  /
Webhook:    POST /webhook
Set Hook:   GET  /set_webhook
"""

import asyncio
import logging
import os
import sqlite3
import traceback

from flask import Flask, render_template, request, jsonify

# --- aiogram imports ---
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import Update

# --- Project imports (handlers, database, config) ---
import config
import database as db
from handlers import router

# =========================================================================
#  SETUP
# =========================================================================

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Database path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "clinic_bot.db")

WEBHOOK_URL = "https://syrio.pythonanywhere.com/webhook"

# --- Dispatcher (created once at module level) ---
dp = Dispatcher()
dp.include_router(router)

# Initialize the database tables on first import
asyncio.run(db.init_db())


# --- Dashboard translations (with table header keys) ---
TRANSLATIONS = {
    'en': {
        'title': '🏥 Clinic Bot Dashboard',
        'quick_stats': 'Quick Stats',
        'total_users': 'Total Users',
        'total_reviews': 'Total Reviews',
        'avg_rating': 'Overall Rating',
        'reg_users': '👥 Registered Users',
        'feedback': '⭐ Feedback & Reviews',
        'filter_label': 'Select a Service Category to Filter:',
        'all_services': 'All Services',
        'detailed_reviews': 'Detailed Reviews',
        'no_reviews': 'No reviews yet for',
        'user': 'User',
        'rating': 'Rating',
        # Table headers — Users
        'th_user_id': 'User ID',
        'th_username': 'Username',
        'th_first_name': 'First Name',
        'th_surname': 'Surname',
        'th_joined_date': 'Joined Date',
        # Table headers — Reviews
        'th_id': 'ID',
        'th_name': 'Name',
        'th_service': 'Service',
        'th_review_text': 'Review Text',
        'th_review_date': 'Review Date',
        'dept_stats': 'Dept Stats',
    },
    'ru': {
        'title': '🏥 Панель управления ботом клиники',
        'quick_stats': 'Краткая статистика',
        'total_users': 'Всего пользователей',
        'total_reviews': 'Всего отзывов',
        'avg_rating': 'Средний рейтинг',
        'reg_users': '👥 Зарегистрированные пользователи',
        'feedback': '⭐ Отзывы и оценки',
        'filter_label': 'Выберите категорию услуг для фильтрации:',
        'all_services': 'Все услуги',
        'detailed_reviews': 'Подробные отзывы',
        'no_reviews': 'Пока нет отзывов для',
        'user': 'Пользователь',
        'rating': 'Оценка',
        # Table headers — Users
        'th_user_id': 'ID пользователя',
        'th_username': 'Имя пользователя',
        'th_first_name': 'Имя',
        'th_surname': 'Фамилия',
        'th_joined_date': 'Дата регистрации',
        # Table headers — Reviews
        'th_id': '№',
        'th_name': 'Имя',
        'th_service': 'Услуга',
        'th_review_text': 'Текст отзыва',
        'th_review_date': 'Дата отзыва',
        'dept_stats': 'Отделения',
    },
    'uz': {
        'title': '🏥 Klinika boti paneli',
        'quick_stats': 'Qisqacha statistika',
        'total_users': 'Jami foydalanuvchilar',
        'total_reviews': 'Jami sharhlar',
        'avg_rating': "O'rtacha reyting",
        'reg_users': "👥 Ro'yxatdan o'tgan foydalanuvchilar",
        'feedback': '⭐ Sharhlar va baholar',
        'filter_label': 'Filtrlash uchun xizmat turini tanlang:',
        'all_services': 'Barcha xizmatlar',
        'detailed_reviews': 'Batafsil sharhlar',
        'no_reviews': "Hozircha sharhlar yo'q:",
        'user': 'Foydalanuvchi',
        'rating': 'Baho',
        # Table headers — Users
        'th_user_id': 'Foydalanuvchi ID',
        'th_username': 'Username',
        'th_first_name': 'Ism',
        'th_surname': 'Familiya',
        'th_joined_date': "Ro'yxatdan o'tgan sana",
        # Table headers — Reviews
        'th_id': '№',
        'th_name': 'Ism',
        'th_service': 'Xizmat',
        'th_review_text': 'Sharh matni',
        'th_review_date': 'Sharh sanasi',
        'dept_stats': 'Bo\'limlar',
    }
}


# =========================================================================
#  HELPER — synchronous DB connection (for the Flask dashboard)
# =========================================================================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================================
#  ROUTE 1 — DASHBOARD  (GET /)
# =========================================================================

@app.route('/')
def dashboard():
    try:
        conn = get_db_connection()

        # Language
        lang = request.args.get('lang', 'en')
        if lang not in TRANSLATIONS:
            lang = 'en'
        t = TRANSLATIONS[lang]

        # Users
        users = conn.execute('SELECT * FROM users').fetchall()
        total_users = len(users)

        # Services dropdown — use lang-independent keys
        services_query = conn.execute(
            'SELECT DISTINCT service_name FROM reviews WHERE service_name IS NOT NULL'
        ).fetchall()
        services = sorted([row['service_name'] for row in services_query if row['service_name']])

        # Filter — 'all' is the sentinel; never a translated string
        selected_service = request.args.get('service', 'all')
        if selected_service not in services:
            selected_service = 'all'

        # Reviews — newest-first
        if selected_service == 'all':
            reviews = conn.execute('''
                SELECT r.id, r.user_id, u.username, u.first_name, u.surname,
                       r.service_name, r.rating, r.review_text, r.review_date
                FROM reviews r
                LEFT JOIN users u ON r.user_id = u.user_id
                ORDER BY r.review_date DESC
            ''').fetchall()
        else:
            reviews = conn.execute('''
                SELECT r.id, r.user_id, u.username, u.first_name, u.surname,
                       r.service_name, r.rating, r.review_text, r.review_date
                FROM reviews r
                LEFT JOIN users u ON r.user_id = u.user_id
                WHERE r.service_name = ?
                ORDER BY r.review_date DESC
            ''', (selected_service,)).fetchall()

        total_reviews_filtered = len(reviews)
        all_reviews_count = conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]

        # Average rating
        avg_rating = 0
        if total_reviews_filtered > 0:
            total_score = sum(r['rating'] for r in reviews if r['rating'])
            avg_rating = round(total_score / total_reviews_filtered, 2)

        conn.close()

        return render_template(
            'dashboard.html',
            users=users,
            reviews=reviews,
            total_users=total_users,
            total_reviews=all_reviews_count,
            filtered_reviews_count=total_reviews_filtered,
            services=services,
            selected_service=selected_service,
            avg_rating=avg_rating,
            lang=lang,
            t=t,
            error=None,
        )
    except Exception as e:
        return render_template(
            'dashboard.html', error=str(e), t=TRANSLATIONS['en'], lang='en'
        )


# =========================================================================
#  ROUTE 2 — DEPARTMENTS DASHBOARD  (GET /departments)
# =========================================================================

DEPT_LABELS = {
    'pediatrician':    {'ru': 'Педиатрия',            'uz': 'Pediatriya',                'en': 'Pediatrics'},
    'neurology':       {'ru': 'Детская неврология',   'uz': 'Bolalar nevrologiyasi',     'en': 'Neurology'},
    'orthopedist':     {'ru': 'Ортопедия',             'uz': 'Ortopediya',                'en': 'Orthopedics'},
    'ent':             {'ru': 'ЛОР',                   'uz': 'LOR',                       'en': 'ENT'},
    'dentist':         {'ru': 'Детская стоматология',  'uz': 'Bolalar stomatologiyasi',   'en': 'Dentistry'},
    'immunology':      {'ru': 'Иммунология',           'uz': 'Immunologiya',              'en': 'Immunology'},
    'gynecology':      {'ru': 'Гинекология',           'uz': 'Ginekologiya',              'en': 'Gynecology'},
    'massage':         {'ru': 'Массаж и физиотерапия', 'uz': 'Massaj va fizioterapiya',   'en': 'Massage & Physio'},
    'laboratory':      {'ru': 'Лаборатория',           'uz': 'Laboratoriya',              'en': 'Laboratory'},
    'neurosonography': {'ru': 'Нейросонография',       'uz': 'Neyrosonografiya',          'en': 'Neurosonography'},
    'uzi':             {'ru': 'УЗИ',                   'uz': 'UZI xizmati',               'en': 'Ultrasound'},
    'procedure':       {'ru': 'Процедурный кабинет',   'uz': 'Muolaja xizmati',           'en': 'Procedures'},
    'allergist':       {'ru': 'Аллергология',          'uz': 'Allergolog',                'en': 'Allergology'},
    'diagnostics':     {'ru': 'Диагностика',           'uz': 'Diagnostika',               'en': 'Diagnostics'},
}

DEPT_UI = {
    'pediatrician':    {'icon': '👶', 'color': '#1D4ED8', 'bg': '#EFF6FF'},
    'neurology':       {'icon': '🧠', 'color': '#7C3AED', 'bg': '#F5F3FF'},
    'orthopedist':     {'icon': '🦴', 'color': '#92400E', 'bg': '#FFFBEB'},
    'ent':             {'icon': '👂', 'color': '#065F46', 'bg': '#ECFDF5'},
    'dentist':         {'icon': '🦷', 'color': '#0E7490', 'bg': '#ECFEFF'},
    'immunology':      {'icon': '🛡️', 'color': '#1D4ED8', 'bg': '#DBEAFE'},
    'gynecology':      {'icon': '🌸', 'color': '#BE185D', 'bg': '#FDF2F8'},
    'massage':         {'icon': '💆', 'color': '#86198F', 'bg': '#FDF4FF'},
    'laboratory':      {'icon': '🧪', 'color': '#065F46', 'bg': '#D1FAE5'},
    'neurosonography': {'icon': '👼', 'color': '#B45309', 'bg': '#FEF3C7'},
    'uzi':             {'icon': '🔊', 'color': '#1E40AF', 'bg': '#DBEAFE'},
    'procedure':       {'icon': '💉', 'color': '#065F46', 'bg': '#ECFDF5'},
    'allergist':       {'icon': '🌿', 'color': '#991B1B', 'bg': '#FEF2F2'},
    'diagnostics':     {'icon': '🔬', 'color': '#3730A3', 'bg': '#EEF2FF'},
}

DEPT_TRANSLATIONS = {
    'en': {
        'title': '🏥 Department Ratings',
        'back': '← Back to Dashboard',
        'dept_overview': 'Department Overview',
        'reviews': 'reviews',
        'no_data': 'No reviews yet',
        'total_users': 'Total Users',
        'total_reviews': 'Total Reviews',
    },
    'ru': {
        'title': '🏥 Рейтинги отделений',
        'back': '← На главную',
        'dept_overview': 'Обзор отделений',
        'reviews': 'отзывов',
        'no_data': 'Пока нет отзывов',
        'total_users': 'Всего пользователей',
        'total_reviews': 'Всего отзывов',
    },
    'uz': {
        'title': '🏥 Bo\'limlar reytingi',
        'back': '← Bosh sahifaga',
        'dept_overview': 'Bo\'limlar sharhi',
        'reviews': 'sharh',
        'no_data': 'Hozircha sharhlar yo\'q',
        'total_users': 'Jami foydalanuvchilar',
        'total_reviews': 'Jami sharhlar',
    },
}

@app.route('/departments')
def departments():
    try:
        conn = get_db_connection()
        lang = request.args.get('lang', 'en')
        if lang not in DEPT_TRANSLATIONS:
            lang = 'en'
        t = DEPT_TRANSLATIONS[lang]

        dept_stats = conn.execute('''
            SELECT service_name,
                   COUNT(*) as review_count,
                   ROUND(AVG(CAST(rating AS FLOAT)), 1) as avg_rating,
                   MIN(rating) as min_rating,
                   MAX(rating) as max_rating
            FROM reviews
            WHERE service_name IS NOT NULL
            GROUP BY service_name
            ORDER BY avg_rating DESC
        ''').fetchall()

        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_reviews = conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]
        conn.close()

        return render_template(
            'departments.html',
            dept_stats=dept_stats,
            dept_labels=DEPT_LABELS,
            dept_ui=DEPT_UI,
            total_users=total_users,
            total_reviews=total_reviews,
            lang=lang,
            t=t,
        )
    except Exception as e:
        return render_template(
            'departments.html', error=str(e),
            dept_stats=[], dept_labels=DEPT_LABELS, dept_ui=DEPT_UI,
            total_users=0, total_reviews=0,
            lang='en', t=DEPT_TRANSLATIONS['en'],
        )


# =========================================================================
#  ROUTE 3 — WEBHOOK LISTENER  (POST /webhook)
# =========================================================================

@app.route('/debug')
def debug():
    results = {}
    # DB tables
    try:
        conn = get_db_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        results['tables'] = [t[0] for t in tables]
        results['bot_states_count'] = conn.execute("SELECT COUNT(*) FROM bot_states").fetchone()[0]
        results['recent_states'] = [
            dict(r) for r in conn.execute(
                "SELECT user_id, state, data FROM bot_states LIMIT 10"
            ).fetchall()
        ]
        conn.close()
        results['db'] = 'ok'
    except Exception as e:
        results['db'] = str(e)
    # Token check
    results['token_set'] = bool(config.BOT_TOKEN)
    results['token_prefix'] = config.BOT_TOKEN[:8] + '...' if config.BOT_TOKEN else None
    return jsonify(results)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive Telegram updates and feed them to the aiogram Dispatcher."""
    try:
        json_data = request.get_json(force=True)
        
        async def process_update():
            # Create fresh session and bot inside the new loop
            session = AiohttpSession(proxy="http://proxy.server:3128")
            bot = Bot(
                token=config.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                session=session,
            )
            # Process the message
            update = Update.model_validate(json_data, context={"bot": bot})
            await dp.feed_update(bot=bot, update=update)
            # Close connection safely
            await session.close()

        asyncio.run(process_update())
        return jsonify({"ok": True}), 200

    except Exception as e:
        logging.error(f"Webhook error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


# =========================================================================
#  ROUTE 4 — SET WEBHOOK  (GET /set_webhook)
# =========================================================================

@app.route('/set_webhook')
def set_webhook():
    """Visit this URL once to register the webhook with Telegram."""
    try:
        async def setup_hook():
            session = AiohttpSession(proxy="http://proxy.server:3128")
            bot = Bot(token=config.BOT_TOKEN, session=session)
            await bot.set_webhook(url=WEBHOOK_URL)
            await session.close()
            
        asyncio.run(setup_hook())
        return f"✅ Webhook successfully set to:<br><code>{WEBHOOK_URL}</code>", 200
        
    except Exception as e:
        return f"❌ Failed to set webhook:<br>{e}", 500


# =========================================================================
#  LOCAL DEVELOPMENT — run with `python app.py`
# =========================================================================

if __name__ == '__main__':
    app.run(debug=True, port=8501)
