import tkinter as tk
from tkinter import ttk, messagebox
from app_state import app_state
import sqlite3
import os
from pathlib import Path
from window_geometry import geometry_for_side_panel, place_geometry_as_trio

class items_window:

    def __init__(self, parent, pos, callback=None, layout="paired"):
        self.parent = parent
        self.state = app_state
        self.callback = callback

        self.tables = {}
        
        self.settings = self.state.settings.copy()
        
        # Получаем цвета и шрифты из настроек
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)
        
        self.window = tk.Toplevel(parent)
        self.window.transient(parent)

        if layout == "trio":
            trio_pos = "left" if pos == "L" else "right"
            place_geometry_as_trio(self.window, 800, 600, pos=trio_pos)
        else:
            w, h, x, y = geometry_for_side_panel(pos, 800, 600)
            self.window.geometry(f"{w}x{h}+{x}+{y}")
        
        # Применяем фон окна
        self.window.configure(bg=self.background_color)
        self.apply_settings_on_startup()
        self.load_databases()
        self.create_widgets(pos)
        # self.window.bind('<Key>', self.press_key)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def apply_settings_on_startup(self):
        from styles import apply_theme
        settings = self.state.settings
        self.window.configure(bg=settings.get('background_color', '#FFFFFF'))
        self.style = ttk.Style()
        apply_theme(self.style, settings)

    def create_custom_styles(self):
        pass

    def load_databases(self):
        db_dir = Path("Databases/items.db")

        if not db_dir.exists():
            messagebox.showerror("Ошибка", "Файл базы данных не найден")
            return
        try:

            with sqlite3.connect(db_dir) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT item FROM {table_name}")
                    items = [item[0] for item in cursor.fetchall()]
                    self.tables[table_name] = items
        
        except Exception as e:
            print(f"Ошибка загрузки БД: {e}")
            self.tables = {}

    def create_widgets(self,pos):

        main_frame = ttk.Frame(self.window, style = "Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_frame = ttk.LabelFrame(main_frame, text="Разделы", padding=10, style = "Custom.TLabelframe")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        self.right_frame = ttk.LabelFrame(main_frame, text="Кнопки", padding=10, style = "Custom.TLabelframe")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.selected_table = tk.StringVar()

        for table_name in self.tables.keys():
            rb = ttk.Radiobutton(
                left_frame,
                text=table_name,  # Название таблицы как есть
                variable=self.selected_table,
                value=table_name,
                command=lambda: self.on_table_selected(pos),
                style = 'TRadiobutton'
            )
            rb.pack(anchor=tk.W, pady=4)

        first_table = list(self.tables.keys())[0]
        self.selected_table.set(first_table)
        self.on_table_selected(pos)

        close_btn = ttk.Button(left_frame, text="Закрыть", command=self.close_window)
        close_btn.pack(anchor=tk.W, pady=(15, 5))

    def on_table_selected(self,pos):
        selected = self.selected_table.get()
        
        # Очищаем правую панель
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        # Получаем товары
        items = self.tables.get(selected, [])
        
        if not items:
            tk.Label(self.right_frame, text="Нет товаров в этой таблице", 
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
                        self.on_item_selected(name, table,pos),
                    style='TButton'
                )
                btn.pack(pady=2, fill=tk.X)
        
        # Настраиваем одинаковые веса для всех колонок
        for col in range(columns_count):
            scrollable_frame.grid_columnconfigure(col, weight=1)
    

    def on_item_selected(self,button_text,category_name,pos):
        if self.callback:
            # Можно получить реальную цену из БД
            price = self.get_item_price(category_name, button_text)
            category_name = pos
            self.callback(button_text, category_name, price)
        else:
            # Для теста (если колбэк не передан)
            messagebox.showinfo(
                "Поломка", 
                f"Категория: {category_name}\nТовар: {button_text}"
            )
    
    def get_item_price(self, category_name, item_name):
        """Получение цены товара из БД"""
        try:
            db_dir = Path("Databases/items.db")
            with sqlite3.connect(db_dir) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT price FROM {category_name} WHERE item = ?", 
                    (item_name,)
                )
                result = cursor.fetchone()
                return result[0] if result else 100  # Значение по умолчанию
        except:
            return 100  # Значение по умолчанию при ошибке

    def press_key(self, event):
        if event.char == '\x1b':
            self.close_window()
    
    def close_window(self):
        self.window.destroy()
