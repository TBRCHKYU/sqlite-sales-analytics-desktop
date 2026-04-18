"""
Улучшенный модальный календарь с сеткой дней.
Используется вместо spinbox/tkcalendar во всех окнах.
"""
import tkinter as tk
from tkinter import messagebox
import calendar
from datetime import datetime

from window_geometry import place_geometry

_MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class CalendarDialog:
    """
    Модальный диалог выбора даты.

    Использование:
        CalendarDialog(parent, date_var,
                       bg_color, text_color, button_color,
                       font_family, font_size)
    После закрытия date_var содержит выбранную дату в формате DD-MM-YYYY.
    """

    def __init__(self, parent, date_var: tk.StringVar,
                 bg_color: str = "#FFFFFF",
                 text_color: str = "#000000",
                 button_color: str = "#444444",
                 font_family: str = "Arial",
                 font_size: int = 11):
        self.date_var = date_var
        self.bg = bg_color
        self.fg = text_color
        self.btn_bg = button_color
        self.font = (font_family, max(9, font_size - 1))
        self.font_bold = (font_family, max(9, font_size - 1), "bold")

        # Парсим текущую дату из переменной
        try:
            current = datetime.strptime(date_var.get(), "%d-%m-%Y")
        except Exception:
            current = datetime.now()

        self.view_year = current.year
        self.view_month = current.month
        self._selected = [current.year, current.month, current.day]

        self.window = tk.Toplevel(parent)
        self.window.title("Выбор даты")
        self.window.resizable(False, False)
        self.window.configure(bg=self.bg)
        self.window.transient(parent)
        self.window.grab_set()

        self._build()
        place_geometry(self.window, 310, 330)
        self.window.lift()
        self.window.focus_force()

    # ------------------------------------------------------------------ build
    def _build(self):
        # Навигация месяц/год
        nav = tk.Frame(self.window, bg=self.bg)
        nav.pack(fill=tk.X, padx=8, pady=(8, 2))

        tk.Button(nav, text="◀", command=self._prev_month,
                  bg=self.btn_bg, fg="white",
                  font=self.font, width=3, relief=tk.FLAT,
                  activebackground=self.btn_bg).pack(side=tk.LEFT)

        self._title_var = tk.StringVar()
        tk.Label(nav, textvariable=self._title_var,
                 bg=self.bg, fg=self.fg, font=self.font_bold).pack(side=tk.LEFT, expand=True)

        tk.Button(nav, text="▶", command=self._next_month,
                  bg=self.btn_bg, fg="white",
                  font=self.font, width=3, relief=tk.FLAT,
                  activebackground=self.btn_bg).pack(side=tk.RIGHT)

        # Заголовок дней недели
        hdr = tk.Frame(self.window, bg=self.bg)
        hdr.pack(fill=tk.X, padx=8, pady=(2, 0))
        for d in _DAYS_RU:
            lbl = tk.Label(hdr, text=d, width=4,
                           bg=self.btn_bg, fg="white", font=self.font,
                           relief=tk.FLAT)
            lbl.pack(side=tk.LEFT, padx=1)

        # Сетка дней
        self._grid = tk.Frame(self.window, bg=self.bg)
        self._grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        for c in range(7):
            self._grid.columnconfigure(c, weight=1)

        # Кнопки внизу
        bar = tk.Frame(self.window, bg=self.bg)
        bar.pack(fill=tk.X, padx=8, pady=(2, 8))
        tk.Button(bar, text="Сегодня", command=self._today,
                  bg="#4CAF50", fg="white",
                  font=self.font, width=9, relief=tk.FLAT).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bar, text="Выбрать", command=self._select,
                  bg=self.btn_bg, fg="white",
                  font=self.font_bold, width=9, relief=tk.FLAT).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bar, text="Отмена", command=self.window.destroy,
                  bg="#808080", fg="white",
                  font=self.font, width=9, relief=tk.FLAT).pack(side=tk.LEFT)

        self._refresh()

    # --------------------------------------------------------------- refresh
    def _refresh(self):
        for w in self._grid.winfo_children():
            w.destroy()

        self._title_var.set(f"{_MONTHS_RU[self.view_month - 1]}  {self.view_year}")

        today = datetime.now()
        first_wd, days_in_month = calendar.monthrange(self.view_year, self.view_month)

        row, col = 0, first_wd
        for day in range(1, days_in_month + 1):
            is_sel = (day == self._selected[2]
                      and self.view_year == self._selected[0]
                      and self.view_month == self._selected[1])
            is_today = (day == today.day
                        and self.view_month == today.month
                        and self.view_year == today.year)

            if is_sel:
                bg, fg = "#1565C0", "white"
            elif is_today:
                bg, fg = "#C8E6C9", self.fg
            elif col >= 5:  # суббота/воскресенье
                bg, fg = self.bg, "#D32F2F"
            else:
                bg, fg = self.bg, self.fg

            btn = tk.Button(
                self._grid, text=str(day), width=4,
                bg=bg, fg=fg, relief=tk.FLAT,
                font=self.font,
                activebackground="#BBDEFB",
                command=lambda d=day: self._click(d),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            self._grid.rowconfigure(row, weight=1)

            col += 1
            if col > 6:
                col = 0
                row += 1

    # ----------------------------------------------------------------- actions
    def _click(self, day: int):
        self._selected = [self.view_year, self.view_month, day]
        self._refresh()

    def _prev_month(self):
        if self.view_month == 1:
            self.view_month, self.view_year = 12, self.view_year - 1
        else:
            self.view_month -= 1
        self._refresh()

    def _next_month(self):
        if self.view_month == 12:
            self.view_month, self.view_year = 1, self.view_year + 1
        else:
            self.view_month += 1
        self._refresh()

    def _today(self):
        t = datetime.now()
        self.view_year, self.view_month = t.year, t.month
        self._selected = [t.year, t.month, t.day]
        self._refresh()

    def _select(self):
        try:
            d = datetime(self._selected[0], self._selected[1], self._selected[2])
            self.date_var.set(d.strftime("%d-%m-%Y"))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Некорректная дата: {e}",
                                 parent=self.window)
            return
        self.window.destroy()
