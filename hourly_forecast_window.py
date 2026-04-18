"""
Окно ML-прогноза по часам (продажи) с учётом графика работы.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app_state import app_state
from window_geometry import place_geometry
from db_queries import SalesAnalyzer
from hourly_forecast_ml import default_forecast_settings, run_hourly_forecast

DOW_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class HourlyForecastWindow:
    """Прогноз суммы продаж по часам (ML)."""

    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.sales_an = SalesAnalyzer()

        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get("button_color", "#000000")
        self.text_color = self.settings.get("text_color", "#FFFFFF")
        self.background_color = self.settings.get("background_color", "#FFFFFF")
        self.font_family = self.settings.get("font_family", "Arial")
        self.font_size = self.settings.get("font_size", 12)

        title = "ML-прогноз продаж по часам"
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.transient(parent)
        place_geometry(self.window, 920, 820)

        self.window.configure(bg=self.background_color)
        self._apply_styles()
        self._build_ui()
        self._load_default_dates()
        self._load_forecast_settings_into_ui()
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
            "Прогноз: HistGradientBoostingRegressor по почасовым суммам из created_at. "
            "Нужны реальные часы в метках времени и не меньше ~14 дней с операциями. "
            "Метрики MAE/RMSE — на отложенных последних днях периода."
        )
        ttk.Label(body, text=note, style="Result.TLabel", wraplength=880).pack(
            anchor=tk.W, pady=(0, 8)
        )

        df = ttk.LabelFrame(body, text="Период истории", style="Custom.TLabelframe", padding=10)
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

        pf = ttk.LabelFrame(body, text="Параметры прогноза", style="Custom.TLabelframe", padding=8)
        pf.pack(fill=tk.X, pady=(0, 8))
        pr = ttk.Frame(pf, style="Custom.TFrame")
        pr.pack(fill=tk.X)
        ttk.Label(pr, text="Дата прогноза (ДД-ММ-ГГГГ):", style="Result.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        self.forecast_date_var = tk.StringVar()
        ttk.Entry(pr, textvariable=self.forecast_date_var, width=14).grid(
            row=0, column=1, padx=6
        )
        ttk.Label(pr, text="Тестовых дней (holdout):", style="Result.TLabel").grid(
            row=0, column=2, padx=(12, 0)
        )
        self.test_days_var = tk.StringVar(value="14")
        ttk.Entry(pr, textvariable=self.test_days_var, width=5).grid(row=0, column=3, padx=4)

        wf = ttk.LabelFrame(body, text="График работы (часы [open, close), 0–23)", style="Custom.TLabelframe", padding=8)
        wf.pack(fill=tk.X, pady=(0, 8))
        wfrow = ttk.Frame(wf, style="Custom.TFrame")
        wfrow.pack(fill=tk.X)
        ttk.Label(wfrow, text="По умолчанию от:", style="Result.TLabel").pack(side=tk.LEFT)
        self.default_open_var = tk.StringVar(value="9")
        tk.Spinbox(wfrow, from_=0, to=23, width=4, textvariable=self.default_open_var).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Label(wfrow, text="до (не включая):", style="Result.TLabel").pack(side=tk.LEFT)
        self.default_close_var = tk.StringVar(value="21")
        tk.Spinbox(wfrow, from_=0, to=23, width=4, textvariable=self.default_close_var).pack(
            side=tk.LEFT, padx=4
        )

        self.use_per_dow_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            wf,
            text="Свой интервал по дням недели",
            variable=self.use_per_dow_var,
            command=self._toggle_per_dow,
        ).pack(anchor=tk.W, pady=(6, 0))

        self.per_dow_frame = ttk.Frame(wf, style="Custom.TFrame")
        self.dow_open_vars: list[tk.StringVar] = []
        self.dow_close_vars: list[tk.StringVar] = []
        for i in range(7):
            row = ttk.Frame(self.per_dow_frame, style="Custom.TFrame")
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=f"{DOW_RU[i]}:", style="Result.TLabel", width=4).pack(
                side=tk.LEFT
            )
            ov = tk.StringVar(value="9")
            cv = tk.StringVar(value="21")
            self.dow_open_vars.append(ov)
            self.dow_close_vars.append(cv)
            tk.Spinbox(row, from_=0, to=23, width=4, textvariable=ov).pack(side=tk.LEFT, padx=2)
            ttk.Label(row, text="—", style="Result.TLabel").pack(side=tk.LEFT)
            tk.Spinbox(row, from_=0, to=23, width=4, textvariable=cv).pack(side=tk.LEFT, padx=2)
        self.per_dow_frame.pack_forget()

        ttk.Button(
            body,
            text="Сохранить график в настройки и рассчитать",
            command=self._run_forecast,
            style="Date.TButton",
        ).pack(anchor=tk.W, pady=(0, 6))

        self.result_frame = ttk.LabelFrame(body, text="Результат", style="Custom.TLabelframe", padding=8)
        self.result_frame.pack(fill=tk.X, pady=(0, 8))
        self.lbl_result = ttk.Label(self.result_frame, text="—", style="Result.TLabel")
        self.lbl_result.pack(anchor=tk.W)

        gf = ttk.LabelFrame(body, text="График: прогноз по часам", style="Custom.TLabelframe", padding=4)
        gf.pack(fill=tk.BOTH, expand=True)
        self._chart_holder = ttk.Frame(gf, style="Custom.TFrame")
        self._chart_holder.pack(fill=tk.BOTH, expand=True)
        self._canvas_widget = None

    def _toggle_per_dow(self):
        if self.use_per_dow_var.get():
            self.per_dow_frame.pack(fill=tk.X, pady=(4, 0))
        else:
            self.per_dow_frame.pack_forget()

    def _load_forecast_settings_into_ui(self):
        fs = self.state.settings.get("forecast_settings")
        if not isinstance(fs, dict):
            fs = default_forecast_settings()
        self.default_open_var.set(str(int(fs.get("default_open_hour", 9))))
        self.default_close_var.set(str(int(fs.get("default_close_hour", 21))))
        per = fs.get("per_dow_hours")
        if isinstance(per, dict) and per:
            self.use_per_dow_var.set(True)
            self.per_dow_frame.pack(fill=tk.X, pady=(4, 0))
            for i in range(7):
                d = per.get(str(i), {})
                if isinstance(d, dict):
                    self.dow_open_vars[i].set(str(int(d.get("open", 9))))
                    self.dow_close_vars[i].set(str(int(d.get("close", 21))))
        else:
            self.use_per_dow_var.set(False)
            self.per_dow_frame.pack_forget()

    def _collect_forecast_settings(self) -> dict:
        fs = {
            "default_open_hour": int(self.default_open_var.get()),
            "default_close_hour": int(self.default_close_var.get()),
            "per_dow_hours": None,
        }
        if self.use_per_dow_var.get():
            per = {}
            for i in range(7):
                per[str(i)] = {
                    "open": int(self.dow_open_vars[i].get()),
                    "close": int(self.dow_close_vars[i].get()),
                }
            fs["per_dow_hours"] = per
        return fs

    def _persist_forecast_settings(self, fs: dict) -> None:
        self.state.settings["forecast_settings"] = fs
        self.state.save_settings()

    def _load_default_dates(self):
        end = datetime.now()
        start = end - timedelta(days=730)
        self.start_var.set(start.strftime("%d-%m-%Y"))
        self.end_var.set(end.strftime("%d-%m-%Y"))
        self.forecast_date_var.set((end + timedelta(days=1)).strftime("%d-%m-%Y"))

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
                nxt = datetime.strptime(mx, "%Y-%m-%d") + timedelta(days=1)
                self.forecast_date_var.set(nxt.strftime("%d-%m-%Y"))
        except Exception:
            self._load_default_dates()

    def _to_db(self, s):
        return self.sales_an.format_date_for_db(s.strip())

    def _run_forecast(self):
        try:
            sd = self._to_db(self.start_var.get())
            ed = self._to_db(self.end_var.get())
            if not sd or not ed:
                messagebox.showwarning("Период", "Укажите даты ДД-ММ-ГГГГ.")
                return
            fd_disp = self.forecast_date_var.get().strip()
            fd_db = self._to_db(fd_disp)
            if not fd_db:
                messagebox.showwarning("Дата прогноза", "Укажите дату прогноза ДД-ММ-ГГГГ.")
                return
            test_days = int(self.test_days_var.get().strip())
            if test_days < 1 or test_days > 120:
                raise ValueError("test_days")
        except ValueError:
            messagebox.showerror("Параметры", "Неверный формат даты или числа тестовых дней.")
            return

        fs = self._collect_forecast_settings()
        if fs["default_open_hour"] >= fs["default_close_hour"] and not self.use_per_dow_var.get():
            messagebox.showwarning(
                "График",
                "Интервал по умолчанию: час открытия должен быть меньше часа закрытия ([open, close)).",
            )
            return

        self._persist_forecast_settings(fs)

        hourly = self.sales_an.get_hourly_sales_totals(sd, ed)

        out = run_hourly_forecast(
            hourly,
            fs,
            period_start=sd,
            period_end=ed,
            test_days=test_days,
            forecast_target_date=fd_db,
        )

        if not out.get("ok"):
            self.lbl_result.configure(text=out.get("error", "Ошибка"))
            self._draw_chart(None)
            messagebox.showinfo("Прогноз", out.get("error", "Нет данных"))
            return

        warn = ""
        if out.get("degenerate_time_warning"):
            warn = "\n\n" + (out.get("degenerate_time_message") or "")

        txt = (
            f"Дата прогноза: {out['forecast_date']}\n"
            f"Сумма по открытым часам: {out['day_total_open_hours']:.0f}\n"
            f"MAE (test): {out['test_mae']:.2f}  RMSE (test): {out['test_rmse']:.2f}\n"
            f"Обучение: {out['train_rows']} строк, тест: {out['test_rows']} "
            f"({out['test_days_used']} дн.)"
        )
        self.lbl_result.configure(text=txt + warn)
        self._draw_chart(out)
        if out.get("degenerate_time_warning"):
            messagebox.showwarning("Время в данных", out.get("degenerate_time_message", ""))

    def _draw_chart(self, out):
        for w in self._chart_holder.winfo_children():
            w.destroy()

        if not out or not out.get("hourly_forecast"):
            ttk.Label(
                self._chart_holder,
                text="Нет данных для графика",
                style="Result.TLabel",
            ).pack(expand=True)
            return

        hf = out["hourly_forecast"]
        hours = [x["hour"] for x in hf]
        preds = [x["predicted"] for x in hf]
        open_mask = [x["is_open"] for x in hf]

        fig = Figure(figsize=(7, 3.4), dpi=100)
        ax = fig.add_subplot(111)
        colors = ["steelblue" if o else "#cccccc" for o in open_mask]
        ax.bar(hours, preds, color=colors, width=0.9, label="Прогноз (синий — открыто)")
        ax.set_xlabel("Час")
        ax.set_ylabel("Прогноз суммы")
        ax.set_xticks(range(0, 24, 2))
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self._chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._canvas_widget = canvas

    def _on_user_close(self):
        try:
            self.window.destroy()
        except tk.TclError:
            pass

    def close_window(self):
        self._on_user_close()
