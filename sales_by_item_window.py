"""
Окно «Продажи по товару»: выбор товара или группы товаров (категории),
показ количества продаж, выручки и графика по датам.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')

from app_state import app_state
from window_geometry import place_geometry
from db_queries import SalesAnalyzer


class SalesByItemWindow:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.analyzer = SalesAnalyzer()

        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)

        self.window = tk.Toplevel(parent)
        self.window.title("Продажи по товару")
        self.window.transient(parent)

        place_geometry(self.window, 1100, 750)

        self.window.configure(bg=self.background_color)
        self.apply_styles()
        self.create_widgets()
        self.load_date_range()
        self.load_items_and_categories()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def apply_styles(self):
        from styles import apply_theme
        self.style = ttk.Style()
        apply_theme(self.style, self.state.settings)

    def create_widgets(self):
        main = ttk.Frame(self.window, style='Custom.TFrame')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Период ---
        period_frame = ttk.LabelFrame(main, text="Период", style='Custom.TLabelframe', padding=10)
        period_frame.pack(fill=tk.X, pady=(0, 10))

        cf = ttk.Frame(period_frame, style='Custom.TFrame')
        cf.pack(fill=tk.X, pady=5)

        ttk.Label(cf, text="С:", style='Result.TLabel').grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.start_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.start_var, width=12).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(cf, text="По:", style='Result.TLabel').grid(row=0, column=2, padx=(15, 5), pady=5, sticky=tk.W)
        self.end_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.end_var, width=12).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        for col, (label, days) in enumerate([("Неделя", 7), ("Месяц", 30), ("Год", 365)], start=4):
            btn = ttk.Button(cf, text=label, command=lambda d=days: self.set_period(d), style='Date.TButton')
            btn.grid(row=0, column=col, padx=5)

        # --- Выбор по товару или по категории ---
        choice_frame = ttk.LabelFrame(main, text="Выбор товаров", style='Custom.TLabelframe', padding=10)
        choice_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value="item")
        ttk.Radiobutton(choice_frame, text="По товарам", variable=self.mode_var, value="item",
                        command=self.on_mode_change, style='Result.TLabel').pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(choice_frame, text="По категориям", variable=self.mode_var, value="category",
                       command=self.on_mode_change, style='Result.TLabel').pack(side=tk.LEFT, padx=5)

        list_frame = ttk.Frame(choice_frame, style='Custom.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=6,
                                  font=(self.font_family, self.font_size),
                                  bg=self.background_color, fg=self.text_color,
                                  selectbackground=self.button_color, selectforeground=self.text_color)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(choice_frame, text="Анализировать", command=self.analyze, style='Date.TButton').pack(pady=(10, 0))

        # --- Результаты: показатели + график ---
        result_frame = ttk.LabelFrame(main, text="Результаты", style='Custom.TLabelframe', padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(result_frame, style='Custom.TFrame')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        stats_frame = ttk.LabelFrame(left, text="Показатели", style='Custom.TLabelframe', padding=10)
        stats_frame.pack(fill=tk.X)

        self.label_count = ttk.Label(stats_frame, text="Количество продаж: —", style='Result.TLabel')
        self.label_count.pack(anchor=tk.W)
        self.label_revenue = ttk.Label(stats_frame, text="Выручка: —", style='Result.TLabel')
        self.label_revenue.pack(anchor=tk.W)

        right = ttk.Frame(result_frame, style='Custom.TFrame')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.graph_frame = ttk.Frame(right, style='Custom.TFrame')
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

        self.graph_placeholder = ttk.Label(self.graph_frame,
                                           text="Выберите товары или категории и нажмите «Анализировать»",
                                           style='Result.TLabel')
        self.graph_placeholder.pack(expand=True)

        ttk.Button(main, text="Закрыть", command=self.close_window, style='Date.TButton').pack(pady=(10, 0))

    def load_date_range(self):
        try:
            min_d, max_d = self.analyzer.get_date_range_stats()
            if min_d and max_d:
                self.start_var.set(self.analyzer.format_date_for_display(min_d))
                self.end_var.set(self.analyzer.format_date_for_display(max_d))
            else:
                t = datetime.now().strftime('%d-%m-%Y')
                self.start_var.set(t)
                self.end_var.set(t)
        except Exception:
            t = datetime.now().strftime('%d-%m-%Y')
            self.start_var.set(t)
            self.end_var.set(t)

    def set_period(self, days):
        end = datetime.now()
        start = end - timedelta(days=days)
        self.start_var.set(start.strftime('%d-%m-%Y'))
        self.end_var.set(end.strftime('%d-%m-%Y'))

    def load_items_and_categories(self):
        try:
            self._items = self.analyzer.get_distinct_items()
            self._categories = self.analyzer.get_distinct_categories()
        except Exception:
            self._items = []
            self._categories = []
        self.on_mode_change()

    def on_mode_change(self):
        self.listbox.delete(0, tk.END)
        if self.mode_var.get() == "category":
            for c in self._categories:
                self.listbox.insert(tk.END, c)
        else:
            for i in self._items:
                self.listbox.insert(tk.END, i)

    def format_date_for_db(self, date_str):
        try:
            if date_str:
                dt = datetime.strptime(date_str.strip(), '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None

    def analyze(self):
        start_s = self.start_var.get().strip()
        end_s = self.end_var.get().strip()
        if not start_s or not end_s:
            messagebox.showwarning("Внимание", "Укажите период (начальную и конечную дату).")
            return

        start_db = self.format_date_for_db(start_s)
        end_db = self.format_date_for_db(end_s)
        if not start_db or not end_db:
            messagebox.showerror("Ошибка", "Формат даты: ДД-ММ-ГГГГ")
            return
        if start_db > end_db:
            messagebox.showwarning("Внимание", "Начальная дата должна быть раньше конечной.")
            return

        selection = [self.listbox.get(i) for i in self.listbox.curselection()]
        if not selection:
            messagebox.showwarning("Внимание", "Выберите хотя бы один товар или одну категорию.")
            return

        try:
            if self.mode_var.get() == "category":
                daily, total_count, total_revenue = self.analyzer.get_sales_by_categories_daily(
                    selection, start_db, end_db)
            else:
                daily, total_count, total_revenue = self.analyzer.get_sales_by_items_daily(
                    selection, start_db, end_db)

            self.label_count.config(text=f"Количество продаж: {total_count}")
            self.label_revenue.config(text=f"Выручка: {total_revenue:,.0f} руб.")

            self.draw_graph(daily)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе: {e}")
            import traceback
            traceback.print_exc()

    def draw_graph(self, daily):
        for w in self.graph_frame.winfo_children():
            w.destroy()

        if not daily:
            ttk.Label(self.graph_frame, text="Нет данных за выбранный период.",
                     style='Result.TLabel').pack(expand=True)
            return

        dates = sorted(daily.keys())
        totals = [float(daily[d]['total']) for d in dates]
        counts = [daily[d]['count'] for d in dates]
        display_dates = [self.analyzer.format_date_for_display(d) for d in dates]

        fig = Figure(figsize=(9, 5), dpi=90)
        fig.patch.set_facecolor('#f0f0f0')
        ax1 = fig.add_subplot(111)

        x = range(len(dates))
        bars = ax1.bar(x, totals, color='steelblue', edgecolor='navy', alpha=0.85)
        ax1.set_ylabel('Выручка (руб.)', fontsize=10)
        ax1.set_xlabel('Дата', fontsize=10)
        ax1.set_title('Выручка по датам', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(display_dates, rotation=45, ha='right')

        for i, v in enumerate(totals):
            if v > 0:
                ax1.text(i, v + (max(totals) * 0.02 if totals else 0), f'{v:,.0f}',
                        ha='center', va='bottom', fontsize=7)

        ax2 = ax1.twinx()
        ax2.plot(x, counts, color='coral', marker='o', markersize=4, linewidth=1.5, label='Кол-во продаж')
        ax2.set_ylabel('Количество продаж', fontsize=10, color='coral')
        ax2.tick_params(axis='y', labelcolor='coral')
        ax2.legend(loc='upper right', fontsize=8)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

    def close_window(self):
        self.window.destroy()
