"""
Создаёт Databases/operations.db, items.db, accounts.db с пустой/демо-схемой
для первого запуска после клонирования. Запуск: python scripts/seed_databases.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "Databases"

ITEM_TABLES = ("common", "unusual", "rare", "legendary", "mythical")

# Небольшой демо-набор товаров (имя, цена, таблица-категория)
DEMO_ITEMS: tuple[tuple[str, int, str], ...] = (
    ("Dough", 60, "common"),
    ("Bread", 30, "common"),
    ("Apple", 15, "unusual"),
    ("Leopard", 100, "rare"),
    ("Crown", 500, "legendary"),
    ("Dragon", 999, "mythical"),
)

ACCOUNT_TABLES = ("main", "reserve")
DEFAULT_STOCK = 50


def _create_operations(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    # created_at с DEFAULT — окно продаж/покупок вставляет без явной даты
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
            account TEXT NOT NULL,
            total_amount INTEGER NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS buyings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
            account TEXT NOT NULL,
            total_amount INTEGER NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS buyings_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL,
            FOREIGN KEY (buy_id) REFERENCES buyings(buy_id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()


def _create_items(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    for table in ITEM_TABLES:
        c.execute(f"CREATE TABLE IF NOT EXISTS {table} (item TEXT, price INTEGER)")
    for name, price, cat in DEMO_ITEMS:
        c.execute(f"INSERT INTO {cat} (item, price) VALUES (?, ?)", (name, price))
    conn.commit()


def _create_accounts(conn: sqlite3.Connection, item_names: list[str]) -> None:
    c = conn.cursor()
    for acc in ACCOUNT_TABLES:
        c.execute(
            f'CREATE TABLE IF NOT EXISTS "{acc}" (item TEXT, quantity INTEGER)'
        )
        for item in item_names:
            c.execute(
                f'INSERT INTO "{acc}" (item, quantity) VALUES (?, ?)',
                (item, DEFAULT_STOCK),
            )
    conn.commit()


def main() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    item_names = [t[0] for t in DEMO_ITEMS]

    ops = DB_DIR / "operations.db"
    items_db = DB_DIR / "items.db"
    acc_db = DB_DIR / "accounts.db"

    for p in (ops, items_db, acc_db):
        if p.exists():
            p.unlink()

    with sqlite3.connect(ops) as conn:
        _create_operations(conn)
    with sqlite3.connect(items_db) as conn:
        _create_items(conn)
    with sqlite3.connect(acc_db) as conn:
        _create_accounts(conn, item_names)

    print(f"OK: {ops.name}, {items_db.name}, {acc_db.name} в {DB_DIR}")


if __name__ == "__main__":
    main()
