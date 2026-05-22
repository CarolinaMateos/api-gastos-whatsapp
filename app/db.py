import sqlite3
from pathlib import Path

DB_PATH = Path("data/expenses.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_expense(user_phone, amount, category, description, raw_message):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses (
                user_phone,
                amount,
                category,
                description,
                raw_message
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_phone, amount, category, description, raw_message)
        )

        return {
            "id": cursor.lastrowid,
            "user_phone": user_phone,
            "amount": amount,
            "category": category,
            "description": description,
            "raw_message": raw_message,
        }


def get_today_expenses(user_phone):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM expenses
            WHERE user_phone = ?
              AND date(created_at) = date('now')
            ORDER BY created_at DESC
            """,
            (user_phone,)
        ).fetchall()

        return [dict(row) for row in rows]


def get_monthly_summary(user_phone):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                category,
                SUM(amount) AS total
            FROM expenses
            WHERE user_phone = ?
              AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_phone,)
        ).fetchall()

        return [dict(row) for row in rows]
    
def delete_last_expense(user_phone):
    with get_connection() as connection:
        row = connection.execute(
            """ 
            SELECT *
            FROM expenses
            WHERE user_phone = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_phone,)
        ).fetchone()
        
        if row is None:
            return None
        
        expense = dict(row)
        
        connection.execute(
            """
            DELETE FROM expenses
            WHERE id = ?
            """,
            (expense["id"],)
        )
        
        return expense