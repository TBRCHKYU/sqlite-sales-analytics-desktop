import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from window_geometry import place_geometry
import sqlite3
import re
import time

class SQLEditorWindow:
    def __init__(self, parent, db_name=None):
        self.parent = parent
        self.db_name = db_name
        self.current_db = None
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"SQL Editor - {db_name}" if db_name else "SQL Editor")
        place_geometry(self.window, 1200, 700)
        
        # Стили
        self.bg_color = '#2b2b2b'
        self.text_bg = '#3c3f41'
        self.text_fg = '#a9b7c6'
        self.button_bg = '#4e5254'
        self.button_fg = '#ffffff'
        self.success_color = '#4CAF50'
        self.error_color = '#f44336'
        
        self.window.configure(bg=self.bg_color)
        
        # Загружаем базу данных если указана
        if db_name:
            self.load_database(db_name)
        
        self.create_widgets()
        self.create_menu()
        
    def load_database(self, db_name):
        db_path = Path(f"Databases/{db_name}.db")
        try:
            self.current_db = sqlite3.connect(db_path)
            self.current_db.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
            self.window.title(f"SQL Editor - {db_name}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить базу данных: {e}")
            self.current_db = None
    
    def create_widgets(self):
        # Основной контейнер
        main_frame = tk.Frame(self.window, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Верхняя панель с базой данных
        top_frame = tk.Frame(main_frame, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Выбор базы данных
        tk.Label(top_frame, text="База данных:", 
                bg=self.bg_color, fg='white').pack(side=tk.LEFT, padx=(0, 5))
        
        self.db_var = tk.StringVar(value=self.db_name if self.db_name else "")
        self.db_combo = ttk.Combobox(top_frame, textvariable=self.db_var, width=30)
        self.db_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.load_databases_list()
        
        # Кнопка подключения
        connect_btn = tk.Button(top_frame, text="Подключиться", 
                               command=self.connect_to_database,
                               bg=self.button_bg, fg=self.button_fg,
                               relief=tk.FLAT)
        connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка получения таблиц
        tables_btn = tk.Button(top_frame, text="Список таблиц",
                              command=self.show_tables,
                              bg=self.button_bg, fg=self.button_fg,
                              relief=tk.FLAT)
        tables_btn.pack(side=tk.LEFT, padx=10)
        
        # Разделитель
        sep = tk.Frame(main_frame, height=2, bg='#555555')
        sep.pack(fill=tk.X, padx=5, pady=5)
        
        # Область редактора SQL
        editor_frame = tk.Frame(main_frame, bg=self.bg_color)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - редактор SQL
        left_panel = tk.Frame(editor_frame, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(left_panel, text="SQL Запрос:", 
                bg=self.bg_color, fg='white', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Текстовое поле для SQL с подсветкой синтаксиса
        self.sql_editor = scrolledtext.ScrolledText(
            left_panel, 
            bg=self.text_bg, 
            fg=self.text_fg,
            insertbackground='white',
            font=('Consolas', 11),
            wrap=tk.NONE,
            height=10
        )
        self.sql_editor.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Подсказки синтаксиса
        syntax_frame = tk.Frame(left_panel, bg=self.bg_color)
        syntax_frame.pack(fill=tk.X, pady=(5, 0))
        
        syntax_label = tk.Label(syntax_frame, 
                               text="Ctrl+Enter - выполнение запроса",
                               bg=self.bg_color, fg='#888888', font=('Arial', 9))
        syntax_label.pack(side=tk.LEFT)
        
        # Кнопки выполнения
        execute_frame = tk.Frame(left_panel, bg=self.bg_color)
        execute_frame.pack(fill=tk.X, pady=(10, 0))
        
        execute_btn = tk.Button(execute_frame, text="Выполнить",
                               command=self.execute_query,
                               bg=self.success_color, fg='white',
                               font=('Arial', 10, 'bold'),
                               relief=tk.FLAT, padx=20, pady=5)
        execute_btn.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(execute_frame, text="Очистить",
                             command=self.clear_editor,
                             bg=self.button_bg, fg=self.button_fg,
                             relief=tk.FLAT, padx=10)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Правая панель - результаты
        right_panel = tk.Frame(editor_frame, bg=self.bg_color)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_panel, text="Результаты:", 
                bg=self.bg_color, fg='white', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Notebook для разных вкладок результатов
        self.result_notebook = ttk.Notebook(right_panel)
        self.result_notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Вкладка с таблицей
        self.table_frame = tk.Frame(self.result_notebook, bg=self.bg_color)
        self.result_notebook.add(self.table_frame, text="Таблица")
        
        # Вкладка с текстом
        self.text_frame = tk.Frame(self.result_notebook, bg=self.bg_color)
        self.result_notebook.add(self.text_frame, text="Текст")
        
        # Вкладка с сообщениями
        self.message_frame = tk.Frame(self.result_notebook, bg=self.bg_color)
        self.result_notebook.add(self.message_frame, text="Сообщения")
        
        self.message_text = scrolledtext.ScrolledText(
            self.message_frame,
            bg=self.text_bg,
            fg=self.text_fg,
            font=('Consolas', 10),
            height=10
        )
        self.message_text.pack(fill=tk.BOTH, expand=True)
        self.message_text.config(state=tk.DISABLED)
        
        # Привязываем горячие клавиши
        self.sql_editor.bind('<Control-Return>', lambda e: self.execute_query())
        self.sql_editor.bind('<Control-KeyRelease>', self.on_key_release)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        """Создает меню"""
        menubar = tk.Menu(self.window, bg=self.bg_color, fg='white')
        self.window.config(menu=menubar)
        # Меню Помощь
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg='white')
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="Справка", command=self.show_help)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def load_databases_list(self):
        """Загружает список доступных баз данных"""
        db_dir = Path("Databases")
        if db_dir.exists():
            db_files = list(db_dir.glob("*.db"))
            db_names = [db.stem for db in db_files]
            self.db_combo['values'] = db_names
    
    def connect_to_database(self):
        """Подключается к выбранной базе данных"""
        db_name = self.db_var.get()
        if not db_name:
            messagebox.showwarning("Внимание", "Выберите базу данных")
            return
        
        self.load_database(db_name)
        if self.current_db:
            self.log_message(f"Подключено к базе данных: {db_name}")
    
    def execute_query(self):
        """Выполняет SQL запрос"""
        if not self.current_db:
            messagebox.showwarning("Внимание", "Сначала подключитесь к базе данных")
            return
        
        sql = self.sql_editor.get("1.0", tk.END).strip()
        if not sql:
            messagebox.showwarning("Внимание", "Введите SQL запрос")
            return
        
        try:
            cursor = self.current_db.cursor()
            
            # Разделяем запросы по точке с запятой
            queries = [q.strip() for q in sql.split(';') if q.strip()]
            
            for query in queries:
                self.log_message(f"Выполнение: \n >>> {query[:100]}")
                
                cursor.execute(query)
                
                # Если запрос возвращает данные (SELECT)
                if query.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    
                    # Отображаем результаты
                    self.show_results_table(columns, rows)
                    self.show_results_text(columns, rows)
                    
                    self.log_message(f"Успешно! Получено {len(rows)} записей")
                
                # Для других запросов (INSERT, UPDATE, DELETE, CREATE, etc.)
                else:
                    self.current_db.commit()
                    affected = cursor.rowcount
                    
                    # Показываем сообщение
                    self.clear_results()
                    self.log_message(f"Успешно! Затронуто строк: {affected}")
        
        except sqlite3.Error as e:
            error_msg = f"Ошибка SQL: {e}"
            self.log_message(error_msg, error=True)
            messagebox.showerror("Ошибка SQL", str(e))
        except Exception as e:
            error_msg = f"Ошибка: {e}"
            self.log_message(error_msg, error=True)
    
    def show_results_table(self, columns, rows):
        # Очищаем фрейм таблицы
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Создаем Treeview
        tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        
        # Настраиваем колонки
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, minwidth=50)
        
        # Добавляем данные
        for row in rows:
            tree.insert('', tk.END, values=row)
        
        # Добавляем прокрутку
        scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_results_text(self, columns, rows):
        # Очищаем фрейм текста
        for widget in self.text_frame.winfo_children():
            widget.destroy()
        
        # Создаем текстовое поле
        text_widget = scrolledtext.ScrolledText(
            self.text_frame,
            bg=self.text_bg,
            fg=self.text_fg,
            font=('Consolas', 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Формируем текст
        if columns and rows:
            # Заголовки
            header = " | ".join(columns)
            text_widget.insert(tk.END, header + "\n")
            text_widget.insert(tk.END, "-" * len(header) + "\n")
            
            # Данные
            for row in rows:
                text_widget.insert(tk.END, " | ".join(str(cell) for cell in row) + "\n")
            
            # Подсчет
            text_widget.insert(tk.END, f"\nВсего записей: {len(rows)}\n")
    
    def clear_results(self):
        """Очищает результаты"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        for widget in self.text_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.table_frame, text="Нет данных для отображения",
                bg=self.bg_color, fg='white').pack(expand=True)
        tk.Label(self.text_frame, text="Нет данных для отображения",
                bg=self.bg_color, fg='white').pack(expand=True)
    
    def show_tables(self):
        """Показывает список таблиц в базе данных"""
        if not self.current_db:
            messagebox.showwarning("Внимание", "Сначала подключитесь к базе данных")
            return
        
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        self.sql_editor.delete("1.0", tk.END)
        self.sql_editor.insert("1.0", query)
        self.execute_query()
        self.sql_editor.delete("1.0", tk.END)
    
    def log_message(self, message, error=False):
        """Добавляет сообщение в лог"""
        self.message_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        
        if error:
            self.message_text.insert(tk.END, f"[{timestamp}] ERROR: {message}\n", "error")
        else:
            self.message_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)
    
    def clear_editor(self):
        """Очищает редактор SQL"""
        self.sql_editor.delete("1.0", tk.END)
    
    def show_help(self):
        """Показывает справку"""
        help_text = """SQL Editor - Справка

Основные функции:
1. Выберите базу данных из списка и нажмите "Подключиться"
2. Введите SQL запрос в редакторе
3. Нажмите Ctrl+Enter или кнопку "Выполнить"

- Список таблиц - показывает все таблицы в БД

Поддерживаемые SQL команды:
SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP, ALTER
"""
        messagebox.showinfo("Справка", help_text)
    
    def show_about(self):
        """Показывает информацию о программе"""
        about_text = """SQL Editor

Редактор SQL запросов для работы с базами данных SQLite.

Возможности:
- Выполнение SQL запросов
- Просмотр таблиц и данных
- Сохранение и загрузка запросов
- Форматирование SQL кода

"""
        messagebox.showinfo("О программе", about_text)
    
    def on_key_release(self, event):
        """Обработка нажатий клавиш для подсветки"""
        # Простая подсветка SQL
        pass
    
    def on_closing(self):
        """Закрытие окна"""
        if self.current_db:
            self.current_db.close()
        self.window.destroy()