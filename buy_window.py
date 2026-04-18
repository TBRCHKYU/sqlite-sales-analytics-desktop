import tkinter as tk
from tkinter import ttk, messagebox
from app_state import app_state
from items_window import items_window
from window_geometry import place_geometry_as_pair
from pathlib import Path
import sqlite3
import os
import time

class sell_window:

    def __init__(self, parent, name):

        self.parent = parent
        self.name = name
        
        # Используем глобальное состояние приложения
        self.state = app_state

        
        # Загружаем текущие настройки
        self.settings = self.state.settings.copy()

        self.style = ttk.Style()
        
        # Получаем цвета и шрифты из настроек
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)
        
        self.window = tk.Toplevel(parent)
        self.window.transient(parent)
        place_geometry_as_pair(self.window, 800, 600, side="right")
        
        # Применяем фон окна
        self.window.configure(bg=self.background_color)
        self.set_window(name)
        if name == "Продажи":
            name = "Покупка"
        else:
            name = "Продажа"
        self.create_custom_styles()
        self.create_widgets(name)
        self.window.bind('<Key>', self.press_key)
        self.window.protocol("WM_DELETE_WINDOW", self.main_menu)

        info_win = items_window(self.window, "L", self.on_item_selected_callback)

    def set_window(self, name):
        self.window.title(name)

    def create_custom_styles(self):
        from styles import apply_theme
        apply_theme(self.style, self.state.settings)

    def create_widgets(self, name):
        # Основной фрейм с фоном
        main_frame = tk.Frame(self.window, bg=self.background_color, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Левая панель - Управление
        left_frame = tk.LabelFrame(
            main_frame, 
            text="Управление", 
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
            padx=10, 
            pady=10
        )
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        db_dir = Path("Databases/accounts.db")
        accounts = []
        self.selected_account = tk.StringVar(value  = "Default")

        with sqlite3.connect(db_dir) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
        for i in tables:
            accounts += [i]

        accs_combo = ttk.Combobox(
            left_frame, 
            textvariable=self.selected_account,
            values=accounts,
            state="readonly",
            width=40
        )
        accs_combo.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        self.input_btn = tk.Button(
            left_frame, 
            text="\nВвод\n", 
            command=self.input_action,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size, 'bold'),
            width=15,
            height=3
        )
        self.input_btn.grid(row=2, column=0, rowspan=2, pady=(0,15), sticky="nsew")

        # Кнопка Главная (серая для визуального различия)
        self.main_menu_btn = tk.Button(
            left_frame, 
            text="Главная", 
            command=self.main_menu,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            width=15,
            height=2
        )
        self.main_menu_btn.grid(row=6, column=0, pady=30, sticky=(tk.W, tk.E))

        self.main_menu_btn = tk.Button(
            left_frame, 
            text="Список", 
            command=self.items,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            width=15,
            height=2
        )
        self.main_menu_btn.grid(row=7, column=0, pady=30, sticky=(tk.W, tk.E))

        # Правая панель - Выбранные товары
        right_frame = tk.LabelFrame(
            main_frame, 
            text="Выбранные товары", 
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
            padx=10, 
            pady=10
        )
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        columns = ("Товар", "Цена")
        self.tree = ttk.Treeview(
            right_frame, 
            columns=columns, 
            show="headings", 
            height=15,
            style='Treeview'
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Панель итого
        total_frame = tk.Frame(right_frame, bg=self.background_color)
        total_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Метка Итого с настройками цвета
        self.total_label = tk.Label(
            total_frame, 
            text="Итого: 0 руб.", 
            font=(self.font_family, 12, "bold"),
            bg=self.background_color,
            fg=self.text_color
        )
        self.total_label.grid(row=0, column=0, sticky=tk.W)

        # Фрейм для кнопок
        btn_frame = tk.Frame(total_frame, bg=self.background_color)
        btn_frame.grid(row=0, column=1, sticky=tk.E)
        
        # Кнопка Очистить с настройками цвета
        self.clear_btn = tk.Button(
            btn_frame, 
            text="Очистить", 
            command=self.clear_list,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, 10)
        )
        self.clear_btn.grid(row=0, column=0, padx=5)
        
        # Кнопка Удалить с настройками цвета
        self.remove_btn = tk.Button(
            btn_frame, 
            text="Удалить", 
            command=self.remove_item,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, 10)
        )
        self.remove_btn.grid(row=0, column=1)

        # Настройка расширения
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

    def press_key(self, event):
        if event.char == '\x1b':
            self.main_menu()

    def items(self):
        info_win = items_window(self.window, "L", self.on_item_selected_callback)

    def clear_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.total_label.config(text="Итого: 0 руб.")

    def remove_item(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления!")
            return
        self.tree.delete(selection[0])
    
    def input_action(self):

        def get_item_category(item_name):
            with sqlite3.connect('Databases/items.db') as conn:
                cursor = conn.cursor()

                # Ищем товар в разных таблицах
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT item FROM {table_name} WHERE item = ?", (item_name,))
                    if cursor.fetchone():
                        return table_name  # Название таблицы = категория

        def prepare_data():
            selected_account = self.selected_account.get()

            items_data = []
            for child in self.tree.get_children():
                values = self.tree.item(child)['values']
                item_name = values[0]
                price = values[1]
                items_data.append({
                    'товар': item_name,
                    'цена': price
                })
            total_amount = sum(item['цена'] for item in items_data)
            sale_id = f"S{int(time.time())}"
            if not items_data:
                messagebox.showwarning("Внимание", "Добавьте товары!")
                return
            
            save_data(selected_account,items_data,total_amount,sale_id)

        def save_data(selected_account,items_data,total_amount,sale_id):

            with sqlite3.connect('Databases/operations.db') as conn:
                cursor = conn.cursor()

                cursor.execute("ATTACH DATABASE 'Databases/accounts.db' AS account_db")

                if self.name == "Продажи":

                    cursor.execute('''
                    INSERT INTO sales (sale_id, account, total_amount)
                    VALUES (?, ?, ?)
                    ''', (sale_id, selected_account, total_amount))

                    for item in items_data:
                        category = get_item_category(item['товар'])
                        cursor.execute('''
                        INSERT INTO sales_items (sale_id, item_name, category, price)
                        VALUES (?, ?, ?, ?)
                    ''', (sale_id, item['товар'], category, item['цена']))

                        cursor.execute(f'''
                            UPDATE account_db.{selected_account} 
                            SET quantity = quantity - 1 
                            WHERE item = ?
                        ''', (item['товар'],))


                else:

                    cursor.execute('''
                        INSERT INTO buyings (buy_id, account, total_amount)
                        VALUES (?, ?, ?)
                    ''', (sale_id, selected_account, total_amount))

                    for item in items_data:
                        category = get_item_category(item['товар'])
                        cursor.execute('''
                        INSERT INTO buyings_items (buy_id, item_name, category, price)
                        VALUES (?, ?, ?, ?)
                    ''', (sale_id, item['товар'], category, item['цена']))

                        cursor.execute(f'''
                            UPDATE account_db.{selected_account} 
                            SET quantity = quantity + 1 
                            WHERE item = ?
                        ''', (item['товар'],))
                self.clear_list()
                        

        prepare_data()


    def on_item_selected_callback(self, item_name, category_name, price=None):
        """Колбэк для добавления товара в таблицу"""
        # Можно получить цену из базы данных или использовать фиксированную
        price = price or 100  # Получайте реальную цену из БД
        
        self.tree.insert("", tk.END, values=(item_name, price))
        self.update_total()

    def update_total(self):
        """Обновление итоговой суммы"""
        total_sum = 0
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            total_sum += values[1]
        self.total_label.config(text=f"Итого: {total_sum} руб.")

    def main_menu(self):
        if messagebox.askyesno("Выход","Вы точно выйти в меню?"):
            self.window.destroy()