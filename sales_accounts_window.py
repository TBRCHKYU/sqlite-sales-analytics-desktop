import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.patches import Rectangle

from app_state import app_state
from window_geometry import place_geometry
from db_queries import SalesAnalyzer

class AccountsAnalysisWindow:
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
        self.window.title("Анализ продаж по аккаунтам")
        self.window.transient(parent)
        
        place_geometry(self.window, 1200, 800)
        
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

        for text, days in [("Сегодня", 0), ("Неделя", 7), ("Месяц", 30), ("Год", 365), ("Все время", -1)]:
            ttk.Button(row2, text=text,
                       command=lambda d=days: self.set_period(days=d),
                       style='Date.TButton').pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(row2, text="Анализировать", command=self.analyze_accounts,
                   style='Date.TButton').pack(side=tk.LEFT, padx=(16, 0))
        
        # Основная область с Notebook (вкладками)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Вкладка 1: Сводная статистика
        self.summary_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.summary_frame, text="Сводная статистика")
        self.create_summary_tab()
        
        # Вкладка 2: Детальный анализ по аккаунтам
        self.details_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.details_frame, text="Детальный анализ")
        self.create_details_tab()

        # Вкладка 3: Сравнение аккаунтов
        self.comparison_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.comparison_frame, text="Сравнение аккаунтов")
        self.create_comparison_tab()

        # Кнопка закрытия
        close_btn = ttk.Button(main_frame, text="Закрыть",
                              command=self.close_window,
                              style='Date.TButton')
        close_btn.pack(pady=(10, 0))
    
    def create_summary_tab(self):
        """Создает вкладку со сводной статистикой"""
        # Создаем Treeview для отображения статистики
        columns = ("Показатель", "Значение", "Дополнительно")
        self.summary_tree = ttk.Treeview(self.summary_frame, columns=columns, 
                                        show="headings", height=20)
        
        for col in columns:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, width=200)
        
        # Добавляем прокрутку
        scrollbar = ttk.Scrollbar(self.summary_frame, orient=tk.VERTICAL, 
                                 command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)
        
        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_details_tab(self):
        """Создает вкладку с детальным анализом"""
        # Панель управления
        details_control_frame = ttk.Frame(self.details_frame, style='Custom.TFrame')
        details_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_control_frame, text="Показать топ:", 
                 style='Result.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        
        self.top_n_var = tk.IntVar(value=10)
        top_n_combo = ttk.Combobox(details_control_frame, 
                                  textvariable=self.top_n_var,
                                  values=[5, 10, 15, 20, 25, 50, "Все"],
                                  width=10,
                                  state="readonly")
        top_n_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Treeview для детального анализа
        detail_columns = ("Ранг", "Аккаунт", "Общая сумма", "Кол-во транзакций", 
                         "Средний чек", "Месяцев активности", "Первая транзакция", 
                         "Последняя транзакция")
        
        self.details_tree = ttk.Treeview(self.details_frame, columns=detail_columns,
                                        show="headings", height=15)
        
        for col in detail_columns:
            self.details_tree.heading(col, text=col)
            self.details_tree.column(col, width=120)
        
        # Добавляем прокрутки
        details_scroll_y = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL,
                                       command=self.details_tree.yview)
        details_scroll_x = ttk.Scrollbar(self.details_frame, orient=tk.HORIZONTAL,
                                       command=self.details_tree.xview)
        
        self.details_tree.configure(yscrollcommand=details_scroll_y.set,
                                  xscrollcommand=details_scroll_x.set)
        
        self.details_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        details_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        details_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_timeline_tab(self):
        """Создает вкладку с временной шкалой"""
        # Фрейм для графика
        self.timeline_graph_frame = ttk.Frame(self.timeline_frame, style='Custom.TFrame')
        self.timeline_graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заглушка
        self.timeline_placeholder = ttk.Label(self.timeline_graph_frame,
                                            text="Выберите период и нажмите 'Анализировать'",
                                            style='Result.TLabel')
        self.timeline_placeholder.pack(expand=True)
    
    def create_comparison_tab(self):
        """Создает вкладку для сравнения аккаунтов (топ-10 по сумме)"""
        self.comparison_graph_frame = ttk.Frame(self.comparison_frame, style='Custom.TFrame')
        self.comparison_graph_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        ttk.Label(self.comparison_graph_frame,
                  text="Выберите период и нажмите «Анализировать»",
                  style='Result.TLabel').pack(expand=True)
    
    def load_date_range(self):
        """Загрузка диапазона дат из базы данных"""
        try:
            min_date, max_date = self.analyzer.get_date_range_stats()
            if min_date and max_date:
                # Преобразуем в формат DD-MM-YYYY для отображения
                self.start_date_var.set(self.analyzer.format_date_for_display(min_date))
                self.end_date_var.set(self.analyzer.format_date_for_display(max_date))
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
        """Показывает календарь для выбора начальной даты"""
        self.show_calendar(self.start_date_var)
    
    def show_end_calendar(self):
        """Показывает календарь для выбора конечной даты"""
        self.show_calendar(self.end_date_var)
    
    def show_calendar(self, date_var):
        from calendar_widget import CalendarDialog
        CalendarDialog(self.window, date_var,
                       self.background_color, self.text_color,
                       self.button_color, self.font_family, self.font_size)
    
    def set_period(self, days=0):
        """Устанавливает период относительно текущей даты"""
        end_date = datetime.now()
        
        if days == -1:  # Все время
            min_date, max_date = self.analyzer.get_date_range_stats()
            if min_date and max_date:
                self.start_date_var.set(self.analyzer.format_date_for_display(min_date))
                self.end_date_var.set(self.analyzer.format_date_for_display(max_date))
                return
        
        if days == 0:
            start_date = end_date
        else:
            start_date = end_date - timedelta(days=days)
        
        self.start_date_var.set(start_date.strftime('%d-%m-%Y'))
        self.end_date_var.set(end_date.strftime('%d-%m-%Y'))
    
    def analyze_accounts(self):
        """Анализ продаж по аккаунтам за выбранный период"""
        start_date_display = self.start_date_var.get()
        end_date_display = self.end_date_var.get()
        
        # Валидация дат
        if not start_date_display or not end_date_display:
            messagebox.showwarning("Внимание", "Выберите начальную и конечную даты")
            return
        
        try:
            # Преобразуем даты в формат для БД
            start_date_db = self.analyzer.format_date_for_db(start_date_display)
            end_date_db = self.analyzer.format_date_for_db(end_date_display)
            
            # Проверка формата дат
            datetime.strptime(start_date_db, '%Y-%m-%d')
            datetime.strptime(end_date_db, '%Y-%m-%d')
            
            # Проверка что начальная дата не позже конечной
            if start_date_db > end_date_db:
                messagebox.showwarning("Внимание", 
                                      "Начальная дата должна быть раньше конечной")
                return
            
            account_sales = self.analyzer.get_account_sales_summary(start_date_db, end_date_db)
            account_metrics = self.analyzer.get_account_performance_metrics(start_date_db, end_date_db)
            comparison_data = self.analyzer.get_account_comparison_data(start_date_db, end_date_db)

            self.display_summary(account_sales, account_metrics, start_date_db, end_date_db)
            self.display_details(account_metrics)
            self.display_comparison(comparison_data)
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректный формат даты. Используйте ДД-ММ-ГГГГ: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе данных: {e}")
            import traceback
            traceback.print_exc()
    
    def display_summary(self, account_sales, account_metrics, start_date, end_date):
        """Отображение сводной статистики"""
        # Очищаем Treeview
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        # Общая статистика
        total_sales = sum(acc['total'] for acc in account_sales.values())
        account_count = len(account_sales)
        transaction_count = sum(acc['count'] for acc in account_sales.values())
        
        # Рассчитываем дни в периоде
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_in_period = (end_dt - start_dt).days + 1
        except:
            days_in_period = 1
        
        avg_daily = total_sales / days_in_period if days_in_period > 0 else 0
        avg_per_account = total_sales / account_count if account_count > 0 else 0
        
        # Топ аккаунты
        sorted_accounts = sorted(account_sales.items(), 
                               key=lambda x: x[1]['total'], 
                               reverse=True)
        top_3_accounts = sorted_accounts[:3]
        
        # Заполняем статистику
        self.summary_tree.insert("", "end", values=("Общая статистика", "", ""))
        self.summary_tree.insert("", "end", values=("  Общая сумма продаж", f"{total_sales:,.0f} руб.", ""))
        self.summary_tree.insert("", "end", values=("  Количество аккаунтов", account_count, ""))
        self.summary_tree.insert("", "end", values=("  Общее количество транзакций", transaction_count, ""))
        self.summary_tree.insert("", "end", values=("  Среднедневная сумма", f"{avg_daily:,.0f} руб.", ""))
        self.summary_tree.insert("", "end", values=("  Средняя сумма на аккаунт", f"{avg_per_account:,.0f} руб.", ""))
        self.summary_tree.insert("", "end", values=("", "", ""))
        
        self.summary_tree.insert("", "end", values=("Топ 3 аккаунта", "Сумма", "Кол-во транзакций"))
        for i, (account, data) in enumerate(top_3_accounts, 1):
            percent = (data['total'] / total_sales * 100) if total_sales > 0 else 0
            self.summary_tree.insert("", "end", 
                                   values=(f"  {i}. {account}", 
                                          f"{data['total']:,.0f} руб. ({percent:.1f}%)",
                                          data['count']))
        self.summary_tree.insert("", "end", values=("", "", ""))
        
        # Метрики эффективности
        if account_metrics:
            active_accounts = sum(1 for acc in account_metrics if acc['transaction_count'] >= 2)
            high_value_accounts = sum(1 for acc in account_metrics if acc['total_amount'] > avg_per_account * 2)
            
            self.summary_tree.insert("", "end", values=("Метрики эффективности", "", ""))
            self.summary_tree.insert("", "end", values=("  Активных аккаунтов (≥2 транзакций)", active_accounts, f"{active_accounts/account_count*100:.1f}%"))
            self.summary_tree.insert("", "end", values=("  Высокоэффективных аккаунтов", high_value_accounts, f"{high_value_accounts/account_count*100:.1f}%"))
            self.summary_tree.insert("", "end", values=("  Средний срок активности", 
                                                      f"{sum(acc['days_active'] for acc in account_metrics)/account_count:.1f} дней",
                                                      ""))
    
    def display_details(self, account_metrics):
        """Отображение детальной информации по аккаунтам"""
        # Очищаем Treeview
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        # Определяем количество отображаемых аккаунтов
        try:
            top_n = self.top_n_var.get()
            if top_n == "Все":
                display_metrics = account_metrics
            else:
                display_metrics = account_metrics[:top_n]
        except:
            display_metrics = account_metrics[:10]
        
        # Заполняем данными
        for i, acc in enumerate(display_metrics, 1):
            # Форматируем даты
            first_date = self.format_date_short(acc['first_transaction']) if acc['first_transaction'] else "-"
            last_date = self.format_date_short(acc['last_transaction']) if acc['last_transaction'] else "-"
            
            self.details_tree.insert("", "end", 
                                   values=(i,
                                          acc['account'],
                                          f"{acc['total_amount']:,.0f}",
                                          acc['transaction_count'],
                                          f"{acc['avg_transaction']:,.0f}",
                                          acc['active_months'],
                                          first_date,
                                          last_date))
    
    def display_timeline(self, monthly_timeline):
        """Отображение временной шкалы продаж"""
        # Очищаем предыдущие графики
        for widget in self.timeline_graph_frame.winfo_children():
            widget.destroy()
        
        if not monthly_timeline:
            ttk.Label(self.timeline_graph_frame,
                     text="Нет данных для отображения",
                     style='Result.TLabel').pack(expand=True)
            return
        
        # Создаем фигуру с графиком
        fig = Figure(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('#f0f0f0')
        
        ax = fig.add_subplot(111)
        
        # Подготовка данных
        months = list(monthly_timeline.keys())
        sales = [monthly_timeline[m]['total'] for m in months]
        account_counts = [monthly_timeline[m]['account_count'] for m in months]
        
        # Форматируем названия месяцев для отображения
        display_months = [self.analyzer.format_year_month(m) for m in months]
        
        # Создаем столбчатую диаграмму
        x = np.arange(len(months))
        width = 0.35
        
        # Основные столбцы - продажи
        bars1 = ax.bar(x - width/2, sales, width, label='Сумма продаж', color='skyblue', edgecolor='black')
        
        # Вторичная ось для количества аккаунтов
        ax2 = ax.twinx()
        bars2 = ax2.bar(x + width/2, account_counts, width, label='Количество аккаунтов', color='lightcoral', edgecolor='black', alpha=0.7)
        
        # Настройка осей
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Сумма продаж (руб.)', color='blue')
        ax2.set_ylabel('Количество активных аккаунтов', color='red')
        
        # Устанавливаем подписи месяцев
        ax.set_xticks(x)
        ax.set_xticklabels(display_months, rotation=45, ha='right')
        
        # Добавляем легенду
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Добавляем сетку
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Настраиваем layout
        fig.tight_layout()
        
        # Встраиваем график в Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.timeline_graph_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем toolbar для навигации
        toolbar = NavigationToolbar2Tk(canvas, self.timeline_graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def display_comparison(self, comparison_data):
        """Отображение сравнения аккаунтов"""
        # Очищаем предыдущие графики
        for widget in self.comparison_graph_frame.winfo_children():
            widget.destroy()
        
        if not comparison_data['top_accounts']:
            ttk.Label(self.comparison_graph_frame,
                     text="Нет данных для сравнения",
                     style='Result.TLabel').pack(expand=True)
            return
        
        # Создаем фигуру с несколькими графиками
        fig = Figure(figsize=(14, 8), dpi=100)
        fig.patch.set_facecolor('#f0f0f0')
        
        # 1. Круговая диаграмма распределения продаж
        ax1 = fig.add_subplot(221)
        
        accounts = list(comparison_data['top_accounts'].keys())
        totals = [comparison_data['top_accounts'][acc]['total'] for acc in accounts]
        
        # Создаем круговую диаграмму
        wedges, texts, autotexts = ax1.pie(totals, labels=accounts, autopct='%1.1f%%',
                                          startangle=90, textprops={'fontsize': 8})
        ax1.set_title('Распределение продаж по топ-аккаунтам', fontsize=10, fontweight='bold')
        
        # 2. Столбчатая диаграмма сравнения
        ax2 = fig.add_subplot(222)
        
        x_pos = np.arange(len(accounts))
        colors = plt.cm.Set3(np.arange(len(accounts)) / len(accounts))
        
        bars = ax2.bar(x_pos, totals, color=colors, edgecolor='black')
        ax2.set_xlabel('Аккаунты')
        ax2.set_ylabel('Сумма продаж (руб.)')
        ax2.set_title('Сравнение сумм продаж', fontsize=10, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(accounts, rotation=45, ha='right')
        if totals:
            ax2.set_ylim(0, max(totals) * 1.15)
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:,.0f}', ha='center', va='bottom', fontsize=8, clip_on=True)
        
        # 3. Линейный график динамики по месяцам (для топ-5 аккаунтов)
        if comparison_data['monthly_data'] and comparison_data['all_months']:
            ax3 = fig.add_subplot(212)
            
            top_5_accounts = list(comparison_data['monthly_data'].keys())[:5]
            months = comparison_data['all_months']
            
            # Форматируем месяцы для отображения
            display_months = [self.analyzer.format_year_month(m) for m in months]
            
            for i, account in enumerate(top_5_accounts):
                account_data = comparison_data['monthly_data'][account]
                monthly_totals = [account_data.get(m, 0) for m in months]
                
                ax3.plot(display_months, monthly_totals, marker='o', label=account, linewidth=2)
            
            ax3.set_xlabel('Месяц')
            ax3.set_ylabel('Сумма продаж (руб.)')
            ax3.set_title('Динамика продаж по месяцам (топ-5 аккаунтов)', fontsize=10, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
        
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.comparison_graph_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.comparison_graph_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def format_date_short(self, date_str):
        """Форматирует дату в короткий формат"""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m.%Y')
        except:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d.%m.%Y')
            except:
                return date_str
    
    def close_window(self):
        """Закрытие окна"""
        self.window.destroy()