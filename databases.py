import tkinter as tk
from tkinter import ttk, messagebox
from app_state import app_state
from window_geometry import place_geometry
from pathlib import Path
import sqlite3
import os
import time
from SQL_Editor import SQLEditorWindow

class databases_window:
    def __init__(self, parent):

        self.tables = {}
        self.parent = parent
        self.state = app_state
        self.settings = self.state.settings.copy()

        self.style = ttk.Style()

        # Получаем цвета и шрифты из настроек
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)

        self.window = tk.Toplevel(parent)
        self.window.title("Базы данных")
        self.window.transient(parent)
        place_geometry(self.window, 700, 500)
        self.window.configure(bg=self.background_color)
        self.load_databases()
        self.create_custom_styles()
        self.create_widgets()
        self.window.bind('<Key>', self.press_key)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        # parent (главное меню) — чтобы закрытие одного окна не закрывало другое
        db_win = SQLEditorWindow(parent)

    def create_custom_styles(self):
        from styles import apply_theme
        apply_theme(self.style, self.state.settings)
    
    def load_databases(self):
        db_dir = Path("Databases")
        
        # Проверяем существование папки
        if not db_dir.exists() or not db_dir.is_dir():
            messagebox.showerror("Ошибка", f"Папка '{db_dir}' не найдена")
            self.tables = {}
            return
        
        db_files = list(db_dir.glob("*.db"))
        
        if not db_files:
            messagebox.showerror("Ошибка", f"В папке '{db_dir}' не найдены файлы .db")
            self.tables = {}
            return
        
        for db_file in db_files:
            database = db_file.stem
            db_dir = Path(db_file)
            with sqlite3.connect(db_dir) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                items = [item[0] for item in cursor.fetchall()]
                self.tables[database]= items
                    
    
    def create_widgets(self):
        bg_color = self.settings.get('background_color', '#FFFFFF')

        main_frame = tk.Frame(self.window, bg=bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.LabelFrame(main_frame, text="Базы данных", padding=10, style="Custom.TLabelframe")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        self.right_frame = ttk.LabelFrame(main_frame, text="Таблицы", padding=10, style="Custom.TLabelframe")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.selected_table = tk.StringVar()

        for database in self.tables.keys():
            rb = ttk.Radiobutton(
                left_frame,
                text=database,
                variable=self.selected_table,
                value=database,
                command=self.on_table_selected,  # ИСПРАВЛЕНО: без круглых скобок
                style='TRadiobutton'
            )
            rb.pack(anchor=tk.W, pady=4)

        # Устанавливаем первую базу данных как выбранную
        if self.tables:
            first_database = list(self.tables.keys())[0]
            self.selected_table.set(first_database)
            self.on_table_selected()  # Вызываем вручную для отображения таблиц первой БД

        close_btn = ttk.Button(left_frame, text="Закрыть", command=self.close_window)
        close_btn.pack(anchor=tk.W, pady=(15, 5))

    def on_table_selected(self):
        selected = self.selected_table.get()
        
        # Очищаем правую панель
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        # Получаем товары
        items = self.tables.get(selected, [])
        
        if not items:
            tk.Label(self.right_frame, text="Нет таблиц", 
                    bg=self.background_color, fg=self.text_color).pack(pady=20)
            return
        
        # Создаем Canvas с прокруткой (если нужно)
        canvas = tk.Canvas(self.right_frame, bg=self.background_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=canvas.yview)
        
        scrollable_frame = ttk.Frame(canvas, style = "Custom.TFrame")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Разбиваем на 3 колонки
        columns_count = 3
        items_per_column = (len(items) + columns_count - 1) // columns_count
        
        # Создаем фреймы для каждой колонки
        for col in range(columns_count):
            column_frame = ttk.Frame(scrollable_frame)
            column_frame.grid(row=0, column=col, padx=10, sticky="n")
            
            # Добавляем кнопки в эту колонку
            start_idx = col * items_per_column
            end_idx = min(start_idx + items_per_column, len(items))
            
            for i in range(start_idx, end_idx):
                item_name = items[i]
                btn = ttk.Button(
                    column_frame,
                    text=item_name,
                    command=lambda name=item_name, table=selected: 
                        self.on_item_selected(name, table),
                    style='TButton'
                )
                btn.pack(pady=2, fill=tk.X)
        
        # Настраиваем одинаковые веса для всех колонок
        for col in range(columns_count):
            scrollable_frame.grid_columnconfigure(col, weight=1)
    

    def on_item_selected(self,table_name,db_name):
        table_window = tk.Toplevel(self.window)
        table_window.title(f"{db_name} - {table_name}")
        table_window.configure(bg=self.settings.get('background_color', '#FFFFFF'))
        place_geometry(table_window, 1000, 600)

        style = ttk.Style()
        
        # Подключаемся к базе данных
        db_file = Path(f"Databases/{db_name}.db")
        try:
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # Получаем названия колонок
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                # Получаем все данные из таблицы
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Создаем фрейм с прокруткой
                main_frame = ttk.Frame(table_window)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Создаем Treeview
                tree = ttk.Treeview(
                    main_frame, 
                    columns=columns,
                    show='headings',
                    height=25,
                    style = "Treeview"
                )
                
                # Настраиваем колонки
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=100, minwidth=50)
                
                # Добавляем данные
                for row in rows:
                    tree.insert('', tk.END, values=row)
                
                # Добавляем прокрутку
                scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Добавляем информационную метку
                info_label = ttk.Label(
                    table_window,
                    text=f"Записей: {len(rows)} | Колонок: {len(columns)}"
                )
                info_label.pack(side=tk.BOTTOM, pady=5)

                bottom_frame = tk.Frame(table_window, bg=self.background_color, padx=10, pady=10)
                bottom_frame.pack(side=tk.BOTTOM, pady=5)
                
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить таблицу: {e}")

    def press_key(self, event):
        if event.char == '\x1b':
            self.close_window()
    
    def close_window(self):
        self.window.destroy()