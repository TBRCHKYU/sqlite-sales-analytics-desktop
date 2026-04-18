import tkinter as tk
from tkinter import ttk, messagebox
from buy_window import sell_window
from trade_window import trade_window
from inform_window import inform_window
from settings_window import SettingsWindow
from databases import databases_window
from app_state import app_state
from window_geometry import place_geometry
from styles import apply_theme

MAIN_MIN_W = 640
MAIN_MIN_H = 520

class MainMenu:
    def __init__(self):
        # Используем глобальное состояние приложения
        self.state = app_state
        
        self.root = tk.Tk()
        self.root.title("Главное меню")

        place_geometry(self.root, 800, 600, min_w=MAIN_MIN_W, min_h=MAIN_MIN_H)

        self.open_windows = {}

        # Применяем настройки перед созданием интерфейса
        self.apply_settings_on_startup()

        self.create_top_panel()
        self.create_operations_panel()
        self.create_bottom_panel()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        
    def apply_settings_on_startup(self):
        """Применение настроек при запуске приложения"""
        settings = self.state.settings

        # Устанавливаем цвет фона главного окна
        bg_color = settings.get('background_color', '#FFFFFF')
        self.root.configure(bg=bg_color)
        
        self.style = ttk.Style()
        self.create_custom_styles()
    
    def create_custom_styles(self):
        apply_theme(self.style, self.state.settings)
    
    def create_top_panel(self):
        settings = self.state.settings
        button_color = settings.get('button_color', 'Grey')
        text_color = settings.get('text_color', 'white')
        font_family = settings.get('font_family', 'Arial')
        font_size = settings.get('font_size', 12)
        
        top_frame = tk.Frame(self.root, bg=settings.get('background_color', '#FFFFFF'))
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        buttons = [
            ("Продажа", self.sale),
            ("Покупка", self.purchase),
            ("Обмен", self.trade),
            ("Данные", self.info),
            ("Базы данных", self.data),
            ("Настройки", self.settings),
        ]
        bg = settings.get("background_color", "#FFFFFF")
        row1 = tk.Frame(top_frame, bg=bg)
        row1.pack(fill=tk.X)
        row2 = tk.Frame(top_frame, bg=bg)
        row2.pack(fill=tk.X, pady=(6, 0))

        for i, (text, command) in enumerate(buttons):
            parent_row = row1 if i < 3 else row2
            btn = tk.Button(
                parent_row,
                text=text,
                bg=button_color,
                fg=text_color,
                font=(font_family, font_size, "bold"),
                command=command,
                height=2,
                width=14,
                relief=tk.FLAT,
                bd=0,
                activebackground=button_color,
                activeforeground=text_color,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=3, pady=2, expand=True, fill=tk.X)
    
    def create_operations_panel(self):
        settings = self.state.settings
        bg_color = settings.get('background_color', '#FFFFFF')
        btn_color = button_color = settings.get('button_color', 'Grey')
        
        # Контейнер для Treeview
        tree_container = tk.Frame(self.root, bg=bg_color)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("Время", "Тип", "Аккаунт", "Сумма")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", style = "Treeview")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем тестовые данные
        self.populate_tree_with_sample_data()
    
    def populate_tree_with_sample_data(self):
        """Заполнение таблицы тестовыми данными"""
        sample_data = [
            ("10:30", "Продажа", "Аккаунт 001", "1,500.00 руб."),
            ("11:15", "Покупка", "Аккаунт 002", "2,300.00 руб."),
            ("12:45", "Обмен", "Аккаунт 003", "800.00 руб."),
            ("14:20", "Продажа", "Аккаунт 004", "3,200.00 руб."),
            ("15:10", "Покупка", "Аккаунт 005", "1,100.00 руб."),
        ]
        
        for data in sample_data:
            self.tree.insert("", "end", values=data)
    
    def create_bottom_panel(self):
        settings = self.state.settings
        bg_color = settings.get('background_color', '#FFFFFF')
        text_color = settings.get('text_color', '#000000')
        font_family = settings.get('font_family', 'Arial')
        
        # Используем tk.Frame для возможности изменения фона
        bottom_frame = tk.Frame(self.root, bg=bg_color)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def sale(self):
        if 'sell' in self.open_windows:
            try:
                self.open_windows['sell'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['sell']
        
        sell_win = sell_window(self.root, "Продажи")
        self.open_windows['sell'] = sell_win

        def on_close():
            if 'sell' in self.open_windows:
                del self.open_windows['sell']

        sell_win.window.protocol("WM_DELETE_WINDOW", lambda: [on_close(), sell_win.main_menu()])

    def purchase(self):
        if 'buy' in self.open_windows:
            try:
                self.open_windows['buy'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['buy']
        
        buy_win = sell_window(self.root, "Покупки")
        self.open_windows['buy'] = buy_win

        def on_close():
            if 'buy' in self.open_windows:
                del self.open_windows['buy']

        buy_win.window.protocol("WM_DELETE_WINDOW", lambda: [on_close(), buy_win.main_menu()])

    def trade(self):
        if 'trade' in self.open_windows:
            try:
                self.open_windows['trade'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['trade']
        
        trade_win = trade_window(self.root)
        self.open_windows['trade'] = trade_win

        def on_close():
            if 'trade' in self.open_windows:
                del self.open_windows['trade']

        trade_win.window.protocol("WM_DELETE_WINDOW", lambda: [on_close(), trade_win.main_menu()])

    def info(self):
        if 'info' in self.open_windows:
            try:
                self.open_windows['info'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['info']
        
        info_win = inform_window(self.root)
        self.open_windows['info'] = info_win

    def data(self):
        if 'sql' in self.open_windows:
            try:
                self.open_windows['sql'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['sql']
        
        db_win = databases_window(self.root)
        self.open_windows['sql'] = db_win

        def on_close():
            if 'databases' in self.open_windows:
                del self.open_windows['databases']
    def settings(self):
        if 'sets' in self.open_windows:
            try:
                self.open_windows['sets'].window.lift()
                return
            except tk.TclError:
                del self.open_windows['sets']
        
        # Передаем коллбэк для обновления интерфейса после сохранения настроек
        sets_win = SettingsWindow(self.root, self.on_settings_saved)
        self.open_windows['sets'] = sets_win

        def on_close():
            if 'sets' in self.open_windows:
                del self.open_windows['sets']

        sets_win.window.protocol("WM_DELETE_WINDOW", lambda: [on_close(), sets_win.close_window()])
    
    def on_settings_saved(self, new_settings):
        # Обновляем состояние приложения
        self.state.settings.update(new_settings)
        self.state.save_settings()
        
        # Применяем новые настройки к интерфейсу
        self.apply_new_settings(new_settings)
        
    
    def apply_new_settings(self, settings):
        bg_color = settings.get('background_color', '#FFFFFF')
        text_color = settings.get('text_color', '#000000')
        button_color = settings.get('button_color', 'Grey')
        font_family = settings.get('font_family', 'Arial')
        font_size = settings.get('font_size', 12)
        
        # 1. Обновляем фон главного окна
        self.root.configure(bg=bg_color)
        
        # 2. Обновляем все Frame
        self.update_all_frames(bg_color)
        
        # 3. Обновляем кнопки верхней панели
        self.update_top_panel_buttons(button_color, text_color, font_family, font_size)
        
        # 4. Обновляем нижнюю панель
        self.update_bottom_panel(bg_color, text_color, font_family)
        
        # 5. Обновляем стили Treeview
        self.update_treeview_styles(button_color, text_color)
        
        # 6. Обновляем шрифт для ttk виджетов
        self.style.configure('.', font=(font_family, font_size))
        
        # 7. Обновляем кастомные стили
        self.create_custom_styles()
    
    def update_all_frames(self, bg_color):
        def update_recursive(widget):
            if isinstance(widget, tk.Frame):
                widget.config(bg=bg_color)
            
            # Обновляем дочерние виджеты
            for child in widget.winfo_children():
                update_recursive(child)
        
        update_recursive(self.root)
    
    def update_top_panel_buttons(self, button_color, text_color, font_family, font_size):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):

                def apply_buttons(w):
                    for c in w.winfo_children():
                        if isinstance(c, tk.Button):
                            c.config(
                                bg=button_color,
                                fg=text_color,
                                font=(font_family, font_size, "bold"),
                            )
                        elif isinstance(c, tk.Frame):
                            apply_buttons(c)

                apply_buttons(child)
                break
    
    def update_bottom_panel(self, bg_color, text_color, font_family):
        # Находим нижний Frame (последний в списке детей)
        frames = [child for child in self.root.winfo_children() if isinstance(child, tk.Frame)]
        if len(frames) >= 2:  # У нас должно быть как минимум 2 Frame
            bottom_frame = frames[-1]  # Последний Frame
            
            # Обновляем фон Frame
            bottom_frame.config(bg=bg_color)
            
            # Обновляем Label и кнопки внутри
            for widget in bottom_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(bg=bg_color, fg=text_color, font=(font_family, 10))
                elif isinstance(widget, tk.Button):
                    widget.config(
                        bg=self.state.settings.get('button_color', 'Grey'),
                        fg=text_color,
                        font=(font_family, 10)
                    )
    
    def update_treeview_styles(self, button_color, text_color):
        # Обновляем заголовки Treeview
        self.style.configure(
            'Treeview.Heading',
            background=button_color,
            foreground='white'
        )
        
        # Обновляем сам Treeview
        self.style.configure(
            'Treeview',
            foreground=text_color
        )

    def on_closing(self):
        if messagebox.askyesno("Выход", "Вы точно хотите выйти?"):
            # Закрываем все дочерние окна
            for window_name in list(self.open_windows.keys()):
                try:
                    self.open_windows[window_name].window.destroy()
                except:
                    pass
            
            # Сохраняем позицию и размер окна (опционально)
            try:
                self.state.save_window_position(self.root)
            except:
                pass
            
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainMenu()
    app.run()