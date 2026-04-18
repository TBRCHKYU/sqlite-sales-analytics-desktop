"""
Окно анализа закупок по датам с графиками (аналог sales_analysis_window для покупок).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')

from app_state import app_state
from window_geometry import place_geometry
from db_queries import BuyingsAnalyzer


class BuyingsAnalysisByDateWindow:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.analyzer = BuyingsAnalyzer()
        
        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)
        
        self.window = tk.Toplevel(parent)
        self.window.title("Анализ закупок по датам")
        self.window.transient(parent)
        
        place_geometry(self.window, 1000, 750)
        
        self.window.configure(bg=self.background_color)
        self.apply_styles()
        self.create_widgets()
        self.load_date_range()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def apply_styles(self):
        from styles import apply_theme
        self.style = ttk.Style()
        apply_theme(self.style, self.state.settings)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.window, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        date_frame = ttk.LabelFrame(main_frame, text="Выбор периода", 
                                   style='Custom.TLabelframe', padding=10)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        row1 = ttk.Frame(date_frame, style='Custom.TFrame')
        row1.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(row1, text="Начальная дата:", style='Result.TLabel').pack(side=tk.LEFT, padx=(0, 4))
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(row1, textvariable=self.start_date_var, width=12,
                                          font=(self.font_family, self.font_size))
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(row1, text="📅", command=self.show_start_calendar,
                   width=3, style='Date.TButton').pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Конечная дата:", style='Result.TLabel').pack(side=tk.LEFT, padx=(0, 4))
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(row1, textvariable=self.end_date_var, width=12,
                                        font=(self.font_family, self.font_size))
        self.end_date_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(row1, text="📅", command=self.show_end_calendar,
                   width=3, style='Date.TButton').pack(side=tk.LEFT)

        row2 = ttk.Frame(date_frame, style='Custom.TFrame')
        row2.pack(fill=tk.X, pady=(2, 0))

        for text, days in [("Сегодня", 0), ("Неделя", 7), ("Месяц", 30), ("Год", 365)]:
            ttk.Button(row2, text=text,
                       command=lambda d=days: self.set_period(days=d),
                       style='Date.TButton').pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(row2, text="Анализировать", command=self.analyze_buyings,
                   style='Date.TButton').pack(side=tk.LEFT, padx=(16, 0))
        
        result_frame = ttk.LabelFrame(main_frame, text="Результаты анализа",
                                     style='Custom.TLabelframe', padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(result_frame, style='Custom.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(result_frame, style='Custom.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        stats_frame = ttk.LabelFrame(left_frame, text="Статистика",
                                    style='Custom.TLabelframe', padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Показатель", "Значение")
        self.stats_tree = ttk.Treeview(stats_frame, columns=columns, 
                                      show="headings", height=8)
        
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=150)
        
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, 
                                       command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.graph_frame = ttk.LabelFrame(right_frame, text="Графики",
                                         style='Custom.TLabelframe', padding=10)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
        
        self.graph_placeholder = ttk.Label(self.graph_frame, 
                                          text="Выберите период и нажмите 'Анализировать'",
                                          style='Result.TLabel')
        self.graph_placeholder.pack(expand=True)
        
        close_btn = ttk.Button(main_frame, text="Закрыть",
                              command=self.close_window,
                              style='Date.TButton')
        close_btn.pack(pady=(10, 0))
    
    def format_date_for_display(self, date_str):
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d-%m-%Y')
        except Exception:
            pass
        return date_str
    
    def format_date_for_db(self, date_str):
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        return date_str
    
    def load_date_range(self):
        try:
            min_date, max_date = self.analyzer.get_date_range_stats()
            if min_date and max_date:
                self.start_date_var.set(self.format_date_for_display(min_date))
                self.end_date_var.set(self.format_date_for_display(max_date))
            else:
                today = datetime.now().strftime('%d-%m-%Y')
                self.start_date_var.set(today)
                self.end_date_var.set(today)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить диапазон дат: {e}")
            today = datetime.now().strftime('%d-%m-%Y')
            self.start_date_var.set(today)
            self.end_date_var.set(today)
    
    def show_start_calendar(self):
        self.show_calendar(self.start_date_var)

    def show_end_calendar(self):
        self.show_calendar(self.end_date_var)

    def show_calendar(self, date_var):
        from calendar_widget import CalendarDialog
        CalendarDialog(self.window, date_var,
                       self.background_color, self.text_color,
                       self.button_color, self.font_family, self.font_size)
    
    def set_period(self, days=0):
        end_date = datetime.now()
        if days == 0:
            start_date = end_date
        else:
            start_date = end_date - timedelta(days=days)
        self.start_date_var.set(start_date.strftime('%d-%m-%Y'))
        self.end_date_var.set(end_date.strftime('%d-%m-%Y'))
    
    def analyze_buyings(self):
        """Анализ закупок за выбранный период"""
        start_date_display = self.start_date_var.get()
        end_date_display = self.end_date_var.get()
        
        if not start_date_display or not end_date_display:
            messagebox.showwarning("Внимание", "Выберите начальную и конечную даты")
            return
        
        try:
            start_date_db = self.format_date_for_db(start_date_display)
            end_date_db = self.format_date_for_db(end_date_display)
            
            datetime.strptime(start_date_db, '%Y-%m-%d')
            datetime.strptime(end_date_db, '%Y-%m-%d')
            
            if start_date_db > end_date_db:
                messagebox.showwarning("Внимание", 
                                      "Начальная дата должна быть раньше конечной")
                return
            
            daily_buyings = self.analyzer.get_daily_buyings_summary(start_date_db, end_date_db)
            item_buyings = self.analyzer.get_item_buyings_summary(start_date_db, end_date_db)
            category_buyings = self.analyzer.get_category_buyings_summary(start_date_db, end_date_db)
            
            daily_buyings_display = {}
            for date_key, value in daily_buyings.items():
                if date_key:
                    display_key = self.format_date_for_display(date_key)
                    daily_buyings_display[display_key] = value
            
            self.display_statistics(daily_buyings_display, item_buyings, category_buyings)
            self.display_graphs(daily_buyings_display, item_buyings, category_buyings)
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректный формат даты. Используйте ДД-ММ-ГГГГ: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе данных: {e}")
    
    def display_statistics(self, daily_buyings, item_buyings, category_buyings):
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        total_buyings = sum(daily_buyings.values())
        total_days = len(daily_buyings)
        avg_daily = total_buyings / total_days if total_days > 0 else 0
        
        self.stats_tree.insert("", "end", values=("Общая сумма закупок", f"{total_buyings:,.0f} руб."))
        self.stats_tree.insert("", "end", values=("Количество дней", f"{total_days}"))
        self.stats_tree.insert("", "end", values=("Среднедневная сумма", f"{avg_daily:,.0f} руб."))
        self.stats_tree.insert("", "end", values=("", ""))
        
        self.stats_tree.insert("", "end", values=("Закупки по категориям", ""))
        for category, data in category_buyings.items():
            self.stats_tree.insert("", "end", 
                                 values=(f"  {category}", 
                                        f"{data['total']:,.0f} руб."))
        
        self.stats_tree.insert("", "end", values=("", ""))
        self.stats_tree.insert("", "end", values=("Топ 5 товаров", ""))
        
        sorted_items = sorted(item_buyings.items(), 
                            key=lambda x: x[1]['total'], 
                            reverse=True)
        
        for i, (item, data) in enumerate(sorted_items[:5]):
            self.stats_tree.insert("", "end", 
                                 values=(f"  {i+1}. {item}", 
                                        f"{data['total']:,.0f} руб."))
    
    def display_graphs(self, daily_buyings, item_buyings, category_buyings):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(10, 6), dpi=80)
        fig.patch.set_facecolor('#f0f0f0')
        gs = fig.add_gridspec(2, 1, hspace=0.45)

        ax1 = fig.add_subplot(gs[0])
        if daily_buyings:
            dates = list(daily_buyings.keys())
            totals_float = []
            for v in daily_buyings.values():
                try:
                    totals_float.append(float(v))
                except Exception:
                    totals_float.append(0.0)
            x_positions = range(len(dates))
            ax1.bar(x_positions, totals_float, color='skyblue', edgecolor='black')
            ax1.set_title('Закупки по дням', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Дата')
            ax1.set_ylabel('Сумма (руб.)')
            ax1.set_xticks(x_positions)
            ax1.set_xticklabels(dates, rotation=45, ha='right')
            if totals_float:
                ax1.set_ylim(0, max(totals_float) * 1.15)
            for i, v in enumerate(totals_float):
                if v > 0:
                    ax1.text(i, v + max(totals_float) * 0.01,
                             f'{v:,.0f}', ha='center', va='bottom', fontsize=8, clip_on=True)

        ax2 = fig.add_subplot(gs[1])
        if item_buyings:
            sorted_items = sorted(item_buyings.items(),
                                  key=lambda x: x[1]['total'],
                                  reverse=True)[:10]
            items = [item for item, _ in sorted_items]
            totals = [float(data['total']) for _, data in sorted_items]
            shortened = [it[:12] + '...' if len(it) > 15 else it for it in items]
            colors = plt.cm.tab20c(range(len(shortened)))
            ax2.pie(totals, labels=shortened, autopct='%1.1f%%',
                    startangle=90, colors=colors)
            ax2.set_title('Закупки по товарам (Топ 10)', fontsize=10, fontweight='bold')

        fig.tight_layout()

        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def close_window(self):
        self.window.destroy()
