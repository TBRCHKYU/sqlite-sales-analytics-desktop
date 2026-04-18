import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Dict, Tuple, List
import math
import os
import sqlite3
from pathlib import Path


@dataclass(frozen=True)
class Box:
    title: str
    subtitle: str
    fields: List[str]
    x: int
    y: int
    w: int = 360
    header_h: int = 54
    line_h: int = 18


class SchemaDiagramApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Структура базы данных (схема)")
        self.root.geometry("1200x800")

        self._build_ui()
        self._draw()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(top, text="Схема БД проекта", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.RIGHT)

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(body, bg="#f7f7f7", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.canvas.yview)
        xscroll = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.root.bind("<Control-r>", lambda e: self._redraw())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def _on_canvas_resize(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _redraw(self):
        self.canvas.delete("all")
        self._draw()

    def _draw_box(self, box: Box) -> Dict[str, Tuple[int, int]]:
        x1, y1 = box.x, box.y
        x2, y2 = box.x + box.w, box.y + box.header_h + box.line_h * (len(box.fields) + 1)

        self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="#222", width=2)
        self.canvas.create_rectangle(x1, y1, x2, y1 + box.header_h, fill="#1f2937", outline="#1f2937")
        self.canvas.create_text(
            x1 + 12,
            y1 + 18,
            text=box.title,
            anchor="w",
            fill="white",
            font=("Arial", 12, "bold"),
        )
        self.canvas.create_text(
            x1 + 12,
            y1 + 38,
            text=box.subtitle,
            anchor="w",
            fill="#d1d5db",
            font=("Arial", 9),
        )

        y = y1 + box.header_h + 10
        self.canvas.create_text(x1 + 12, y, text="Поля:", anchor="w", fill="#111827", font=("Arial", 10, "bold"))
        y += box.line_h

        anchors: Dict[str, Tuple[int, int]] = {}
        for f in box.fields:
            self.canvas.create_text(x1 + 18, y, text=f"• {f}", anchor="w", fill="#111827", font=("Consolas", 10))
            anchors[f] = (x1, y)
            y += box.line_h

        anchors["__box_center__"] = ((x1 + x2) // 2, (y1 + y2) // 2)
        anchors["__left__"] = (x1, (y1 + y2) // 2)
        anchors["__right__"] = (x2, (y1 + y2) // 2)
        anchors["__top__"] = ((x1 + x2) // 2, y1)
        anchors["__bottom__"] = ((x1 + x2) // 2, y2)
        return anchors

    def _arrow(self, x1: int, y1: int, x2: int, y2: int, text: str | None = None):
        self.canvas.create_line(x1, y1, x2, y2, fill="#374151", width=2, arrow=tk.LAST, arrowshape=(12, 14, 5))
        if text:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_rectangle(mx - 80, my - 12, mx + 80, my + 12, fill="#f7f7f7", outline="")
            self.canvas.create_text(mx, my, text=text, fill="#111827", font=("Arial", 9))

    def _note(self, x: int, y: int, w: int, text: str):
        x2, y2 = x + w, y + 70
        self.canvas.create_rectangle(x, y, x2, y2, fill="#fff7ed", outline="#fb923c", width=2)
        self.canvas.create_text(x + 10, y + 10, anchor="nw", text=text, fill="#7c2d12", font=("Arial", 10))

    def _try_read_db_info(self) -> str:
        ops = Path("Databases/operations.db")
        items = Path("Databases/items.db")
        accs = Path("Databases/accounts.db")

        present = []
        for p in (ops, items, accs):
            present.append(f"{p.name}: {'есть' if p.exists() else 'нет'}")
        return " | ".join(present)

    def _draw(self):
        self.status_var.set(self._try_read_db_info())

        title = "Проект «Касса»: SQLite базы и связи"
        self.canvas.create_text(20, 18, anchor="w", text=title, font=("Arial", 16, "bold"), fill="#111827")
        self.canvas.create_text(
            20,
            44,
            anchor="w",
            text="Подсказка: Ctrl+R — перерисовать, Esc — закрыть",
            font=("Arial", 10),
            fill="#4b5563",
        )

        boxes: Dict[str, Dict[str, Tuple[int, int]]] = {}

        # operations.db
        boxes["sales"] = self._draw_box(
            Box(
                title="sales",
                subtitle="Databases/operations.db",
                fields=["sale_id (PK)", "created_at", "account", "total_amount"],
                x=40,
                y=90,
            )
        )
        boxes["sales_items"] = self._draw_box(
            Box(
                title="sales_items",
                subtitle="Databases/operations.db",
                fields=["sale_id (FK → sales.sale_id)", "item_name", "category", "price"],
                x=460,
                y=90,
            )
        )

        boxes["buyings"] = self._draw_box(
            Box(
                title="buyings",
                subtitle="Databases/operations.db",
                fields=["buy_id (PK)", "created_at", "account", "total_amount"],
                x=40,
                y=340,
            )
        )
        boxes["buyings_items"] = self._draw_box(
            Box(
                title="buyings_items",
                subtitle="Databases/operations.db",
                fields=["buy_id (FK → buyings.buy_id)", "item_name", "category", "price"],
                x=460,
                y=340,
            )
        )

        # items.db
        boxes["items_db"] = self._draw_box(
            Box(
                title="items.db",
                subtitle="Databases/items.db",
                fields=[
                    "таблицы = категории (например: Напитки, Снеки...)",
                    "в каждой таблице: item, price",
                    "используется для выбора товара и цены",
                ],
                x=40,
                y=600,
                w=780,
            )
        )

        # accounts.db
        boxes["accounts_db"] = self._draw_box(
            Box(
                title="accounts.db",
                subtitle="Databases/accounts.db",
                fields=[
                    "таблицы = аккаунты/склады (например: Default, Account_1...)",
                    "в каждой таблице: item, quantity",
                    "остатки изменяются при продаже/покупке/обмене",
                ],
                x=860,
                y=220,
                w=360,
            )
        )

        # Relations: sales -> sales_items
        self._arrow(
            boxes["sales"]["__right__"][0],
            boxes["sales"]["__right__"][1] - 20,
            boxes["sales_items"]["__left__"][0],
            boxes["sales_items"]["__left__"][1] - 20,
            text="1 : N по sale_id",
        )

        # Relations: buyings -> buyings_items
        self._arrow(
            boxes["buyings"]["__right__"][0],
            boxes["buyings"]["__right__"][1] - 20,
            boxes["buyings_items"]["__left__"][0],
            boxes["buyings_items"]["__left__"][1] - 20,
            text="1 : N по buy_id",
        )

        # Logical relations: items_db -> operations items
        self._arrow(
            boxes["items_db"]["__left__"][0] + 220,
            boxes["items_db"]["__top__"][1],
            boxes["sales_items"]["__bottom__"][0] - 70,
            boxes["sales_items"]["__bottom__"][1],
            text="item/price",
        )
        self._arrow(
            boxes["items_db"]["__left__"][0] + 520,
            boxes["items_db"]["__top__"][1],
            boxes["buyings_items"]["__bottom__"][0] + 70,
            boxes["buyings_items"]["__bottom__"][1],
            text="item/price",
        )

        # Logical relations: operations -> accounts (остатки)
        self._arrow(
            boxes["sales"]["__right__"][0],
            boxes["sales"]["__right__"][1] + 40,
            boxes["accounts_db"]["__left__"][0],
            boxes["accounts_db"]["__left__"][1] - 70,
            text="минус quantity",
        )
        self._arrow(
            boxes["buyings"]["__right__"][0],
            boxes["buyings"]["__right__"][1] + 30,
            boxes["accounts_db"]["__left__"][0],
            boxes["accounts_db"]["__left__"][1] - 20,
            text="плюс quantity",
        )

        self._note(
            x=860,
            y=90,
            w=360,
            text="Примечание:\nСвязи между БД логические.\nОперации пишутся в operations.db,\nа остатки обновляются в accounts.db.",
        )

        self.canvas.configure(scrollregion=(0, 0, 1280, 820))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SchemaDiagramApp().run()
