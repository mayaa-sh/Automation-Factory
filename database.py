import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "factory.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                department TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'متوسط',
                status TEXT NOT NULL DEFAULT 'ثبت‌شده',
                created_at TEXT NOT NULL DEFAULT (
                    datetime('now', 'localtime')
                ),
                due_date TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                note TEXT,
                changed_at TEXT NOT NULL DEFAULT (
                    datetime('now', 'localtime')
                ),
                FOREIGN KEY (request_id)
                    REFERENCES requests(id)
                    ON DELETE CASCADE
            )
        """)


if __name__ == "__main__":
    initialize_database()
    print("پایگاه داده آماده است.")
    print(f"Database path: {DB_PATH}")