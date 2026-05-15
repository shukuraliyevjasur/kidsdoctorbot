import sys, os, tempfile, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
import aiosqlite

pytestmark = pytest.mark.asyncio(loop_scope="function")


async def make_temp_db() -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    async with aiosqlite.connect(tmp.name) as db:
        await db.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT DEFAULT '',
                surname TEXT DEFAULT '',
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE user_language (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uz'
            )
        """)
        await db.execute("""
            CREATE TABLE reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_name TEXT,
                rating INTEGER,
                review_text TEXT,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    return tmp.name


async def test_is_fully_registered_false_when_no_user(monkeypatch):
    import database
    db_path = await make_temp_db()
    monkeypatch.setattr(database, "DB_NAME", db_path)
    assert await database.is_fully_registered(99999) is False
    os.unlink(db_path)


async def test_is_fully_registered_true_when_first_name_set(monkeypatch):
    import database
    db_path = await make_temp_db()
    monkeypatch.setattr(database, "DB_NAME", db_path)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO users (user_id, username, first_name, surname) VALUES (1, 'u', 'Jasur', '')"
        )
        await db.commit()
    assert await database.is_fully_registered(1) is True
    os.unlink(db_path)


async def test_is_fully_registered_false_when_first_name_empty(monkeypatch):
    import database
    db_path = await make_temp_db()
    monkeypatch.setattr(database, "DB_NAME", db_path)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO users (user_id, username, first_name, surname) VALUES (2, 'u', '', '')"
        )
        await db.commit()
    assert await database.is_fully_registered(2) is False
    os.unlink(db_path)
