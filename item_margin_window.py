"""
Рейтинг выгодности товаров: выручка по продажам минус сумма закупок по совпадению наименования.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from app_state import app_state
from window_geometry import place_geometry
from db_queries import get_item_margin_ranking, SalesAnalyzer


_STATUS_TEXT = {
    "both": "Продажи и закупки",
    "sales_only": "Только продажи",
    "buy_only": "Только закупки",
}


class ItemMarginWindow:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.analyzer = SalesAnalyzer()

        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get("button_color", "#000000")
        self.text_color = self.settings.get("text_color", "#FFFFFF")
        self.background_color = self.settings.get("background_color", "#FFFFFF")
        self.font_family = self.settings.get("font_family", "Arial")
        self.font_size = self.settings.get("font_size", 12)

        self.window = tk.Toplevel(parent)
        self.window.title("Рейтинг выгодности товаров")
        self.window.transient(parent)
        place_geometry(self.window, 950, 650)

        self.window.configure(bg=self.background_color)
        self._apply_styles()
        self._build_ui()
        self._load_default_dates()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def _apply_styles(self):
        from styles import apply_theme
        self.style = ttk.Style()
        apply_theme(self.style, self.state.settings)

    def _build_ui(self):
        main = ttk.Frame(self.window, style="Custom.TFrame", padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        hint = (
            "Маржа = сумма строк продаж − сумма строк закупок по одному наименованию товара. "
            "Имена в продажах и закупках должны совпадать."
        )
        ttk.Label(main, text=hint, style="Result.TLabel", wraplength=880).pack(
            anchor=tk.W, pady=(0, 8)
        )

        df = ttk.LabelFrame(main, text="Период", style="Custom.TLabelframe", padding=10)
        df.pack(fill=tk.X, pady=(0, 10))
        cf = ttk.Frame(df, style="Custom.TFrame")
        cf.pack(fill=tk.X)

        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        ttk.Label(cf, text="С:", style="Result.TLabel").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(cf, textvariable=self.start_var, width=12).grid(row=0, column=1, padx=5)
        ttk.Label(cf, text="По:", style="Result.TLabel").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        ttk.Entry(cf, textvariable=self.end_var, width=12).grid(row=0, column=3, padx=5)

        for col, (label, days) in enumerate([("Неделя", 7), ("Месяц", 30), ("Год", 365)], start=4):
            ttk.Button(
                cf,
                text=label,
                command=lambda d=days: self._set_period(d),
                style="Date.TButton",
            ).grid(row=0, column=col, padx=4)

        ttk.Button(
            main,
            text="Построить рейтинг",
            command=self._refresh,
            style="Date.TButton",
        ).pack(anchor=tk.W, pady=(0, 8))

        twrap = ttk.Frame(main, style="Custom.TFrame")
        twrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cols = ("item", "sales", "buy", "margin", "share", "status")
        self.tree = ttk.Treeview(
            twrap,
            columns=cols,
            show="headings",
            height=18,
        )
        self.tree.heading("item", text="Товар")
        self.tree.heading("sales", text="Продажи")
        self.tree.heading("buy", text="Закупки")
        self.tree.heading("margin", text="Маржа")
        self.tree.heading("share", text="Доля от ∑ марж (>0), %")
        self.tree.heading("status", text="Данные")
        self.tree.column("item", width=220)
        self.tree.column("sales", width=100)
        self.tree.column("buy", width=100)
        self.tree.column("margin", width=100)
        self.tree.column("share", width=140)
        self.tree.column("status", width=160)

        sy = ttk.Scrollbar(twrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(main, text="Закрыть", command=self.close_window, style="Date.TButton").pack(
            anchor=tk.W, pady=(0, 0)
        )

    def _load_default_dates(self):
        try:
            min_d, max_d = self.analyzer.get_date_range_stats()
            if min_d and max_d:
                self.start_var.set(self.analyzer.format_date_for_display(min_d))
                self.end_var.set(self.analyzer.format_date_for_display(max_d))
            else:
                t = datetime.now().strftime("%d-%m-%Y")
                self.start_var.set(t)
                self.end_var.set(t)
        except Exception:
            t = datetime.now().strftime("%d-%m-%Y")
            self.start_var.set(t)
            self.end_var.set(t)

    def _set_period(self, days):
        end = datetime.now()
        start = end - timedelta(days=days)
        self.start_var.set(start.strftime("%d-%m-%Y"))
        self.end_var.set(end.strftime("%d-%m-%Y"))

    def _to_db_date(self, s):
        return self.analyzer.format_date_for_db(s.strip())

    def _refresh(self):
        try:
            sd = self._to_db_date(self.start_var.get())
            ed = self._to_db_date(self.end_var.get())
            if not sd or not ed:
                messagebox.showwarning("Период", "Укажите даты в формате ДД-ММ-ГГГГ.")
                return
        except Exception:
            messagebox.showerror("Период", "Неверный формат даты.")
            return

        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            rows = get_item_margin_ranking(sd, ed)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        pos_margin_sum = sum(r["margin"] for r in rows if r["margin"] > 0)

        for r in rows:
            m = r["margin"]
            if pos_margin_sum > 0 and m > 0:
                share = 100.0 * m / pos_margin_sum
                share_s = f"{share:.1f}"
            else:
                share_s = "—"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    r["item_name"],
                    f"{r['sales_total']:.0f}",
                    f"{r['buy_total']:.0f}",
                    f"{m:.0f}",
                    share_s,
                    _STATUS_TEXT.get(r["status"], r["status"]),
                ),
            )

    def close_window(self):
        self.window.destroy()
