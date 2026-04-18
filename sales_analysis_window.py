"""
Окно анализа продаж по датам с графиками
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
from db_queries import SalesAnalyzer


class SalesAnalysisWindow:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.analyzer = SalesAnalyzer()
        
        # Загружаем настройки
        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)
        
        # Создаем окно
        self.window = tk.Toplevel(parent)
        self.window.title("Анализ продаж по датам")
        self.window.transient(parent)
        
        place_geometry(self.window, 1000, 750)
        
        # Применяем настройки
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
        """Создание интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.window, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель - выбор дат
        date_frame = ttk.LabelFrame(main_frame, text="Выбор периода", 
                                   style='Custom.TLabelframe', padding=10)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Строка 1: выбор дат
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

        # Строка 2: быстрые периоды + кнопка анализа
        row2 = ttk.Frame(date_frame, style='Custom.TFrame')
        row2.pack(fill=tk.X, pady=(2, 0))

        for text, days in [("Сегодня", 0), ("Неделя", 7), ("Месяц", 30), ("Год", 365)]:
            ttk.Button(row2, text=text,
                       command=lambda d=days: self.set_period(days=d),
                       style='Date.TButton').pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(row2, text="Анализировать", command=self.analyze_sales,
                   style='Date.TButton').pack(side=tk.LEFT, padx=(16, 0))
        
        # Нижняя панель - результаты и графики
        result_frame = ttk.LabelFrame(main_frame, text="Результаты анализа",
                                     style='Custom.TLabelframe', padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Разделение на две части: статистика и графики
        left_frame = ttk.Frame(result_frame, style='Custom.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(result_frame, style='Custom.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Левая часть - статистика
        stats_frame = ttk.LabelFrame(left_frame, text="Статистика",
                                    style='Custom.TLabelframe', padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview для отображения статистики
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
        
        # Правая часть - графики
        self.graph_frame = ttk.LabelFrame(right_frame, text="Графики",
                                         style='Custom.TLabelframe', padding=10)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Изначально показываем заглушку
        self.graph_placeholder = ttk.Label(self.graph_frame, 
                                          text="Выберите период и нажмите 'Анализировать'",
                                          style='Result.TLabel')
        self.graph_placeholder.pack(expand=True)
        
        # Кнопка закрытия
        close_btn = ttk.Button(main_frame, text="Закрыть",
                              command=self.close_window,
                              style='Date.TButton')
        close_btn.pack(pady=(10, 0))
    
    def format_date_for_display(self, date_str):
        """Форматирует дату из YYYY-MM-DD в DD-MM-YYYY для отображения"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d-%m-%Y')
        except:
            pass
        return date_str
    
    def format_date_for_db(self, date_str):
        """Форматирует дату из DD-MM-YYYY в YYYY-MM-DD для запроса к БД"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        return date_str
    
    def load_date_range(self):
        """Загрузка диапазона дат из базы данных"""
        try:
            min_date, max_date = self.analyzer.get_date_range_stats()
            if min_date and max_date:
                # Преобразуем в формат DD-MM-YYYY для отображения
                self.start_date_var.set(self.format_date_for_display(min_date))
                self.end_date_var.set(self.format_date_for_display(max_date))
            else:
                # Если нет данных, используем текущую дату
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
        """Устанавливает период относительно текущей даты"""
        end_date = datetime.now()
        
        if days == 0:
            start_date = end_date
        else:
            start_date = end_date - timedelta(days=days)
        
        self.start_date_var.set(start_date.strftime('%d-%m-%Y'))
        self.end_date_var.set(end_date.strftime('%d-%m-%Y'))
    
    def analyze_sales(self):
        """Анализ продаж за выбранный период"""
        start_date_display = self.start_date_var.get()
        end_date_display = self.end_date_var.get()
        
        # Валидация дат
        if not start_date_display or not end_date_display:
            messagebox.showwarning("Внимание", "Выберите начальную и конечную даты")
            return
        
        try:
            # Преобразуем даты в формат для БД
            start_date_db = self.format_date_for_db(start_date_display)
            end_date_db = self.format_date_for_db(end_date_display)
            
            # Проверка формата дат
            datetime.strptime(start_date_db, '%Y-%m-%d')
            datetime.strptime(end_date_db, '%Y-%m-%d')
            
            # Проверка что начальная дата не позже конечной
            if start_date_db > end_date_db:
                messagebox.showwarning("Внимание", 
                                      "Начальная дата должна быть раньше конечной")
                return
            
            # Получение данных
            daily_sales = self.analyzer.get_daily_sales_summary(start_date_db, end_date_db)
            item_sales = self.analyzer.get_item_sales_summary(start_date_db, end_date_db)
            category_sales = self.analyzer.get_category_sales_summary(start_date_db, end_date_db)
            
            # Преобразуем ключи дат в формат DD-MM-YYYY для отображения
            daily_sales_display = {}
            for date_key, value in daily_sales.items():
                if date_key:
                    display_key = self.format_date_for_display(date_key)
                    daily_sales_display[display_key] = value
            
            # Отображение статистики
            self.display_statistics(daily_sales_display, item_sales, category_sales)
            
            # Отображение графиков
            self.display_graphs(daily_sales_display, item_sales, category_sales)
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректный формат даты. Используйте ДД-ММ-ГГГГ: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе данных: {e}")
    
    def display_statistics(self, daily_sales, item_sales, category_sales):
        """Отображение статистики в Treeview"""
        # Очищаем Treeview
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Общая статистика
        total_sales = sum(daily_sales.values())
        total_days = len(daily_sales)
        avg_daily = total_sales / total_days if total_days > 0 else 0
        
        self.stats_tree.insert("", "end", values=("Общая сумма продаж", f"{total_sales:,.0f} руб."))
        self.stats_tree.insert("", "end", values=("Количество дней", f"{total_days}"))
        self.stats_tree.insert("", "end", values=("Среднедневная сумма", f"{avg_daily:,.0f} руб."))
        self.stats_tree.insert("", "end", values=("", ""))
        
        # Продажи по категориям
        self.stats_tree.insert("", "end", values=("Продажи по категориям", ""))
        for category, data in category_sales.items():
            self.stats_tree.insert("", "end", 
                                 values=(f"  {category}", 
                                        f"{data['total']:,.0f} руб."))
        
        # Продажи по товарам (топ 5)
        self.stats_tree.insert("", "end", values=("", ""))
        self.stats_tree.insert("", "end", values=("Топ 5 товаров", ""))
        
        sorted_items = sorted(item_sales.items(), 
                            key=lambda x: x[1]['total'], 
                            reverse=True)
        
        for i, (item, data) in enumerate(sorted_items[:5]):
            self.stats_tree.insert("", "end", 
                                 values=(f"  {i+1}. {item}", 
                                        f"{data['total']:,.0f} руб."))
    
    def display_graphs(self, daily_sales, item_sales, category_sales):
        """Отображение графиков"""
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(10, 6), dpi=80)
        fig.patch.set_facecolor('#f0f0f0')
        gs = fig.add_gridspec(2, 1, hspace=0.45)

        # График продаж по дням
        ax1 = fig.add_subplot(gs[0])
        if daily_sales:
            dates = list(daily_sales.keys())
            sales_float = []
            for sale in daily_sales.values():
                try:
                    sales_float.append(float(sale))
                except Exception:
                    sales_float.append(0.0)
            x_positions = range(len(dates))
            ax1.bar(x_positions, sales_float, color='skyblue', edgecolor='black')
            ax1.set_title('Продажи по дням', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Дата')
            ax1.set_ylabel('Сумма (руб.)')
            ax1.set_xticks(x_positions)
            ax1.set_xticklabels(dates, rotation=45, ha='right')
            if sales_float:
                ax1.set_ylim(0, max(sales_float) * 1.15)
            for i, v in enumerate(sales_float):
                if v > 0:
                    ax1.text(i, v + max(sales_float) * 0.01,
                             f'{v:,.0f}', ha='center', va='bottom', fontsize=8, clip_on=True)

        # Продажи по товарам (топ 10)
        ax2 = fig.add_subplot(gs[1])
        if item_sales:
            sorted_items = sorted(item_sales.items(),
                                  key=lambda x: x[1]['total'],
                                  reverse=True)[:10]
            items = [item for item, _ in sorted_items]
            totals = [float(data['total']) for _, data in sorted_items]
            shortened = [it[:12] + '...' if len(it) > 15 else it for it in items]
            colors = plt.cm.tab20c(range(len(shortened)))
            ax2.pie(totals, labels=shortened, autopct='%1.1f%%',
                    startangle=90, colors=colors)
            ax2.set_title('Продажи по товарам (Топ 10)', fontsize=10, fontweight='bold')

        fig.tight_layout()

        # Toolbar пакуется ПЕРВЫМ (снизу), чтобы canvas не перекрывал его
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    
    def close_window(self):
        """Закрытие окна"""
        self.window.destroy()