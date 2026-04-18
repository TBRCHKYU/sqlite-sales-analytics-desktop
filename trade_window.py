import tkinter as tk
from tkinter import ttk, messagebox
from app_state import app_state
from window_geometry import place_geometry_as_trio
from items_window import items_window
from pathlib import Path
import sqlite3

class trade_window:

    def __init__(self,parent):
        self.parent = parent
        self.state = app_state
        # Загружаем текущие настройки
        self.settings = self.state.settings.copy()
        
        # Получаем цвета и шрифты из настроек
        self.button_color = self.settings.get('button_color', '#000000')
        self.text_color = self.settings.get('text_color', '#FFFFFF')
        self.background_color = self.settings.get('background_color', '#FFFFFF')
        self.font_family = self.settings.get('font_family', 'Arial')
        self.font_size = self.settings.get('font_size', 12)

        self.window = tk.Toplevel(parent)
        self.window.transient(parent)

        place_geometry_as_trio(self.window, 800, 600, pos="center")

        self.window.configure(bg=self.background_color)
        self.window.title("Обмен")
        self.create_widgets()
        self.window.bind('<Key>', self.press_key)
        self.window.protocol("WM_DELETE_WINDOW", self.main_menu)
        
        info_win_L = items_window(self.window, "L", self.on_item_selected_callback, layout="trio")
        info_win_R = items_window(self.window, "R", self.on_item_selected_callback, layout="trio")
        
    def create_custom_styles(self):
        from styles import apply_theme
        self.style = ttk.Style()
        apply_theme(self.style, self.state.settings)
    
    def create_widgets(self):

        main_frame = tk.Frame(self.window, bg=self.background_color, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        left_frame = tk.LabelFrame(
            main_frame, 
            text="Отдаю", 
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
            padx=10, 
            pady=10
        )
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5))

        right_frame = tk.LabelFrame(
            main_frame, 
            text="Получаю", 
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
            padx=10, 
            pady=10
        )
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5))

        header = tk.LabelFrame(
            main_frame,
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
            padx=10, 
            pady=10
        )
        header.grid(row=0, column=0, columnspan = 2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5))

        db_dir = Path("Databases/accounts.db")
        accounts = []
        self.selected_account_left = tk.StringVar(value  = "Default")
        self.selected_account_right = tk.StringVar(value  = "Default")

        with sqlite3.connect(db_dir) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
        for i in tables:
            accounts += [i]
        accounts += ['внешний']

        left_accs = ttk.Combobox(
            header, 
            textvariable=self.selected_account_left,
            values=accounts,
            state="readonly",
            width=30
        )
        left_accs.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        right_accs = ttk.Combobox(
            header, 
            textvariable=self.selected_account_right,
            values=accounts,
            state="readonly",
            width=30
        )
        right_accs.grid(row=0, column=2, sticky="nsew", pady=(0, 10))

        self.input_btn = tk.Button(
            header, 
            text="Ввод", 
            command=self.input_action,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size, 'bold'),
            width=15,
            height=3
        )
        self.input_btn.grid(row=0, column=1, padx=(20,20), sticky="nsew")

        columns = ("Товар", "Цена")
        self.left_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15,style='Treeview')
        self.right_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15,style='Treeview')

        for col in columns:
            self.left_tree.heading(col, text=col)
            self.left_tree.column(col, width=120)

            self.right_tree.heading(col, text=col)
            self.right_tree.column(col, width=120)

        left_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.left_tree.yview)
        self.left_tree.configure(yscrollcommand=left_scrollbar.set)
        right_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.right_tree.yview)
        self.right_tree.configure(yscrollcommand=right_scrollbar.set)

        self.left_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.right_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        left_total_frame = tk.LabelFrame(
            left_frame,
            font=(self.font_family, self.font_size, 'bold'),
            bg=self.background_color,
            fg=self.text_color,
        )
        left_total_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        self.left_total_label = tk.Label(
            left_total_frame, 
            text="Итого: 0 руб.", 
            font=(self.font_family, 12, "bold"),
            bg=self.background_color,
            fg=self.text_color
        )
        self.left_total_label.grid(row=0, column=0, sticky=tk.W)

        left_btn_frame = tk.Frame(left_total_frame, bg=self.background_color)
        left_btn_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.left_clear_btn = tk.Button(
            left_btn_frame, 
            text="Очистить", 
            command=self.clear_left_list,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, 10)
        )
        self.left_clear_btn.grid(row=0, column=0, padx=5)
        
        self.left_remove_btn = tk.Button(
            left_btn_frame, 
            text="Удалить", 
            command=self.remove_left_item,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, 10)
        )
        self.left_remove_btn.grid(row=0, column=1)


        right_total_frame = tk.Frame(right_frame, bg=self.background_color)
        right_total_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        self.right_total_label = tk.Label(
            right_total_frame, 
            text="Итого: 0 руб.", 
            font=(self.font_family, 12, "bold"),
            bg=self.background_color,
            fg=self.text_color
        )
        self.right_total_label.grid(row=0, column=0, sticky=tk.W)

        right_btn_frame = tk.Frame(right_total_frame, bg=self.background_color)
        right_btn_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.right_clear_btn = tk.Button(
            right_btn_frame, 
            text="Очистить", 
            command=self.clear_right_list,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
        )
        self.right_clear_btn.grid(row=0, column=0, padx=5)
        
        self.right_remove_btn = tk.Button(
            right_btn_frame, 
            text="Удалить", 
            command=self.remove_right_item,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
        )
        self.right_remove_btn.grid(row=0, column=1)

        bottom_frame = tk.Frame(self.window, bg=self.background_color, padx=10, pady=5)
        bottom_frame.grid(row=2, column=0)

        self.main_menu_btn = tk.Button(
            bottom_frame, 
            text="Главная", 
            command=self.main_menu,
            bg=self.button_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size, 'bold'),
            width=15,
            height=3
        )
        self.main_menu_btn.grid(row=0, column=0, pady=5, sticky=(''))

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=0) 
        right_frame.rowconfigure(0, weight=0)

    def press_key(self, event):
        if event.char == '\x1b':
            self.main_menu()

    def clear_left_list(self):
        for item in self.left_tree.get_children():
            self.left_tree.delete(item)
        self.left_total_label.config(text="Итого: 0 руб.")

    def clear_right_list(self):
        for item in self.right_tree.get_children():
            self.right_tree.delete(item)
        self.right_total_label.config(text="Итого: 0 руб.")

    def remove_left_item(self):
        selection = self.left_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления!")
            return
        self.left_tree.delete(selection[0])

    def remove_right_item(self):
        selection = self.right_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления!")
            return
        self.right_tree.delete(selection[0])
    
    def input_action(self):
        pass
        left_acc = self.selected_account_left.get()
        right_acc = self.selected_account_right.get()

        left_items_data = []
        right_items_data = []

        for child in self.left_tree.get_children():
                values = self.left_tree.item(child)['values']
                item_name = values[0]
                price = values[1]
                left_items_data.append({
                    'товар': item_name,
                    'цена': price
                })
        
        for child in self.right_tree.get_children():
                values = self.right_tree.item(child)['values']
                item_name = values[0]
                price = values[1]
                right_items_data.append({
                    'товар': item_name,
                    'цена': price
                })
        if not left_items_data or not right_items_data:
                messagebox.showwarning("Внимание", "Добавьте товары!")
                return

        with sqlite3.connect('Databases/accounts.db') as conn:
            cursor = conn.cursor()
            
            for item in left_items_data:
                cursor.execute(f'''
                            UPDATE {left_acc} 
                            SET quantity = quantity - 1 
                            WHERE item = ?
                        ''', (item['товар'],))
            for item in right_items_data:
                cursor.execute(f'''
                            UPDATE {left_acc} 
                            SET quantity = quantity + 1 
                            WHERE item = ?
                        ''', (item['товар'],))

            if right_acc == "внешний":
                return

            for item in left_items_data:
                cursor.execute(f'''
                            UPDATE {right_acc} 
                            SET quantity = quantity + 1 
                            WHERE item = ?
                        ''', (item['товар'],))
            for item in right_items_data:
                cursor.execute(f'''
                            UPDATE {right_acc} 
                            SET quantity = quantity - 1 
                            WHERE item = ?
                        ''', (item['товар'],))

    def on_item_selected_callback(self, item_name, category_name, price=None):
        """Колбэк для добавления товара в таблицу"""
        # Можно получить цену из базы данных или использовать фиксированную
        price = price or 100  # Получайте реальную цену из БД
        
        if category_name == "L":
            self.left_tree.insert("", tk.END, values=(item_name, price))
        else:
            self.right_tree.insert("", tk.END, values=(item_name, price))
        self.update_total(category_name)

    def update_total(self,category_name):
        """Обновление итоговой суммы"""
        total_sum = 0
        if category_name == "L":
            for child in self.left_tree.get_children():
                values = self.left_tree.item(child)['values']
                total_sum += values[1]
            self.left_total_label.config(text=f"Итого: {total_sum} руб.")
        else:
            for child in self.right_tree.get_children():
                values = self.right_tree.item(child)['values']
                total_sum += values[1]
            self.right_total_label.config(text=f"Итого: {total_sum} руб.")
    
    def main_menu(self):
        if messagebox.askyesno("Выход","Вы точно хотите выйти?"):
            self.window.destroy()