"""
Окно рекомендаций по запасу на день: сколько единиц товара иметь в наличии,
оценка по истории продаж в тот же день недели.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from app_state import app_state
from window_geometry import place_geometry
from db_queries import SalesAnalyzer
from stock_recommendation import recommend_daily_stock_from_sales_rows

DOW_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class StockRecommendationWindow:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.sales_an = SalesAnalyzer()

        self.settings = self.state.settings.copy()
        self.background_color = self.settings.get("background_color", "#FFFFFF")

        self.window = tk.Toplevel(parent)
        self.window.title("Потребность в товаре на день")
        self.window.transient(parent)
        place_geometry(self.window, 720, 640)
        self.window.configure(bg=self.background_color)

        self._apply_styles()
        self._build_ui()
        self._load_default_dates()
        self.window.protocol("WM_DELETE_WINDOW", self._on_user_close)

    def _apply_styles(self):
        from styles import apply_theme

        self.style = ttk.Style()
        apply_theme(self.style, self.state.settings)

    def _build_ui(self):
        main = ttk.Frame(self.window, style="Custom.TFrame", padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        bottom_bar = ttk.Frame(main, style="Custom.TFrame")
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        ttk.Button(
            bottom_bar,
            text="Закрыть",
            command=self._on_user_close,
            style="Date.TButton",
        ).pack(side=tk.RIGHT)

        body = ttk.Frame(main, style="Custom.TFrame")
        body.pack(fill=tk.BOTH, expand=True)

        note = (
            "Список строится по продажам: для выбранной даты берётся день недели, "
            "по всем таким дням в периоде считается среднее число проданных единиц по каждому наименованию "
            "(одна строка чека = одна единица). Рекомендуемое количество = округление среднего вверх."
        )
        ttk.Label(body, text=note, style="Result.TLabel", wraplength=680).pack(
            anchor=tk.W, pady=(0, 8)
        )

        df = ttk.LabelFrame(body, text="Период истории продаж", style="Custom.TLabelframe", padding=10)
        df.pack(fill=tk.X, pady=(0, 8))
        cf = ttk.Frame(df, style="Custom.TFrame")
        cf.pack(fill=tk.X)
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        ttk.Label(cf, text="С:", style="Result.TLabel").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(cf, textvariable=self.start_var, width=12).grid(row=0, column=1, padx=5)
        ttk.Label(cf, text="По:", style="Result.TLabel").grid(row=0, column=2, padx=(8, 0))
        ttk.Entry(cf, textvariable=self.end_var, width=12).grid(row=0, column=3, padx=5)
        ttk.Button(
            cf,
            text="2 года",
            command=lambda: self._set_period(730),
            style="Date.TButton",
        ).grid(row=0, column=4, padx=6)
        ttk.Button(
            cf,
            text="Весь период",
            command=self._load_full_range,
            style="Date.TButton",
        ).grid(row=0, column=5, padx=4)

        pf = ttk.LabelFrame(body, text="День планирования", style="Custom.TLabelframe", padding=8)
        pf.pack(fill=tk.X, pady=(0, 8))
        pr = ttk.Frame(pf, style="Custom.TFrame")
        pr.pack(fill=tk.X)
        ttk.Label(pr, text="Дата (ДД-ММ-ГГГГ):", style="Result.TLabel").pack(side=tk.LEFT)
        self.target_date_var = tk.StringVar()
        ttk.Entry(pr, textvariable=self.target_date_var, width=14).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            body,
            text="Сформировать список",
            command=self._run,
            style="Date.TButton",
        ).pack(anchor=tk.W, pady=(0, 6))

        hdr = ttk.LabelFrame(body, text="Рекомендация", style="Custom.TLabelframe", padding=6)
        hdr.pack(fill=tk.X, pady=(0, 6))
        self.lbl_header = ttk.Label(hdr, text="—", style="Result.TLabel", wraplength=660)
        self.lbl_header.pack(anchor=tk.W)

        lf = ttk.LabelFrame(body, text="Список (кол-во — наименование)", style="Custom.TLabelframe", padding=4)
        lf.pack(fill=tk.BOTH, expand=True)
        cols = ("qty", "name")
        self.tree = ttk.Treeview(lf, columns=cols, show="headings", height=18)
        self.tree.heading("qty", text="Кол-во")
        self.tree.heading("name", text="Товар")
        self.tree.column("qty", width=70, anchor=tk.E)
        self.tree.column("name", width=520, anchor=tk.W)
        sy = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_default_dates(self):
        end = datetime.now()
        start = end - timedelta(days=365)
        self.start_var.set(start.strftime("%d-%m-%Y"))
        self.end_var.set(end.strftime("%d-%m-%Y"))
        self.target_date_var.set(end.strftime("%d-%m-%Y"))

    def _set_period(self, days):
        end = datetime.now()
        start = end - timedelta(days=days)
        self.start_var.set(start.strftime("%d-%m-%Y"))
        self.end_var.set(end.strftime("%d-%m-%Y"))

    def _load_full_range(self):
        try:
            mn, mx = self.sales_an.get_date_range_stats()
            fmt = self.sales_an.format_date_for_display
            if mn and mx:
                self.start_var.set(fmt(mn))
                self.end_var.set(fmt(mx))
        except Exception:
            self._load_default_dates()

    def _to_db(self, s):
        return self.sales_an.format_date_for_db(s.strip())

    def _run(self):
        try:
            sd = self._to_db(self.start_var.get())
            ed = self._to_db(self.end_var.get())
            td = self._to_db(self.target_date_var.get().strip())
            if not sd or not ed or not td:
                messagebox.showwarning("Даты", "Укажите период и дату в формате ДД-ММ-ГГГГ.")
                return
        except Exception:
            messagebox.showerror("Даты", "Неверный формат даты.")
            return

        rows = self.sales_an.get_daily_item_sales_units(sd, ed)
        out = recommend_daily_stock_from_sales_rows(rows, td)

        for i in self.tree.get_children():
            self.tree.delete(i)

        if not out.get("ok"):
            self.lbl_header.configure(text=out.get("error", "Ошибка"))
            messagebox.showinfo("Список", out.get("error", "Нет данных"))
            return

        try:
            disp = datetime.strptime(td, "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            disp = td
        dow_i = int(out.get("target_weekday_index", 0))
        dow_txt = DOW_RU[dow_i] if 0 <= dow_i < 7 else ""
        n = len(out["items"])
        self.lbl_header.configure(
            text=(
                f"Рекомендуется иметь в наличии на {disp} ({dow_txt}). "
                f"Позиций в списке: {n}. Оценка по продажам в тот же день недели за период {sd} … {ed}."
            )
        )

        for it in out["items"]:
            self.tree.insert("", tk.END, values=(it["recommended_qty"], it["item_name"]))

    def _on_user_close(self):
        try:
            self.window.destroy()
        except tk.TclError:
            pass

    def close_window(self):
        self._on_user_close()
