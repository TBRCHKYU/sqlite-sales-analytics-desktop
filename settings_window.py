import copy
import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser
from app_state import app_state
from window_geometry import place_geometry

class SettingsWindow:
    def __init__(self, parent, on_save_callback=None):
        self.parent = parent
        self.on_save_callback = on_save_callback  # Коллбэк при сохранении
        
        # Используем глобальное состояние приложения
        self.state = app_state
        
        # Загружаем текущие настройки
        self.settings = self.state.settings.copy()
        
        # Создаем окно настроек
        self.window = tk.Toplevel(parent)
        self.window.title("Настройки")

        place_geometry(self.window, 520, 460)
        
        self.window.transient(parent)
        
        # Устанавливаем фон окна настроек
        self.window.configure(bg=self.settings.get('background_color', '#FFFFFF'))
        
        self.create_widgets()
        self.window.bind('<Key>', self.press_key)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def create_widgets(self):
        # Основной фрейм с учетом фона
        bg_color = self.settings.get('background_color', '#FFFFFF')
        main_frame = tk.Frame(self.window, bg=bg_color, padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Шрифт
        font_frame = tk.LabelFrame(
            main_frame, 
            text="Шрифт", 
            padx=10, 
            pady=10,
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000'),
            font=("Arial", 10, "bold")
        )
        font_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        
        # Список шрифтов
        available_fonts = sorted(font.families())
        self.selected_font = tk.StringVar(value=self.settings['font_family'])
        
        font_label = tk.Label(
            font_frame, 
            text="Шрифты:", 
            anchor="w",
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000')
        )
        font_label.pack(anchor="w", pady=(0, 5))
        
        # Комбобокс с шрифтами
        font_combo = ttk.Combobox(
            font_frame, 
            textvariable=self.selected_font,
            values=available_fonts,
            state="readonly",
            width=40
        )
        font_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Пример текста с выбранным шрифтом
        font_preview = tk.Label(
            font_frame, 
            text="Пример текста с выбранным шрифтом",
            font=(self.selected_font.get(), 12),
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000')
        )
        font_preview.pack(anchor="w")
        
        # Обновление превью при выборе шрифта
        def update_font_preview(*args):
            font_preview.config(font=(self.selected_font.get(), 12))
        
        self.selected_font.trace("w", update_font_preview)
        
        # 2. Цвета
        colors_frame = tk.LabelFrame(
            main_frame, 
            text="Цвета", 
            padx=10, 
            pady=10,
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000'),
            font=("Arial", 10, "bold")
        )
        colors_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        
        # Кнопки
        button_frame = tk.Frame(colors_frame, bg=bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_label = tk.Label(
            button_frame, 
            text="Кнопки:", 
            width=15, 
            anchor="w",
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000')
        )
        button_label.pack(side=tk.LEFT)
        
        self.button_color_btn = tk.Button(
            button_frame,
            text=self.get_color_name(self.settings['button_color']),
            bg=self.settings['button_color'],
            fg="#FFFFFF" if self.is_dark_color(self.settings['button_color']) else "#000000",
            command=self.choose_button_color,
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=2
        )
        self.button_color_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Текст
        text_frame = tk.Frame(colors_frame, bg=bg_color)
        text_frame.pack(fill=tk.X, pady=(0, 10))
        
        text_label = tk.Label(
            text_frame, 
            text="Текст:", 
            width=15, 
            anchor="w",
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000')
        )
        text_label.pack(side=tk.LEFT)
        
        self.text_color_btn = tk.Button(
            text_frame,
            text=self.get_color_name(self.settings['text_color']),
            bg=self.settings['text_color'],
            fg="#FFFFFF" if self.is_dark_color(self.settings['text_color']) else "#000000",
            command=self.choose_text_color,
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=2
        )
        self.text_color_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Задний план
        background_frame = tk.Frame(colors_frame, bg=bg_color)
        background_frame.pack(fill=tk.X)
        
        background_label = tk.Label(
            background_frame, 
            text="Задний план:", 
            width=15, 
            anchor="w",
            bg=bg_color,
            fg=self.settings.get('text_color', '#000000')
        )
        background_label.pack(side=tk.LEFT)
        
        self.background_color_btn = tk.Button(
            background_frame,
            text=self.get_color_name(self.settings['background_color']),
            bg=self.settings['background_color'],
            fg="#FFFFFF" if self.is_dark_color(self.settings['background_color']) else "#000000",
            command=self.choose_background_color,
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=2
        )
        self.background_color_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 3. Кнопки управления
        buttons_frame = tk.Frame(main_frame, bg=bg_color)
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=(12, 0))
        
        # Кнопка Сохранить и применить
        save_apply_btn = tk.Button(
            buttons_frame,
            text="Сохранить и применить",
            bg=self.settings['button_color'],
            fg=self.settings['text_color'],
            command=self.save_and_apply_settings,
            width=20,
            height=2,
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            bd=3
        )
        save_apply_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка Сбросить
        reset_btn = tk.Button(
            buttons_frame,
            text="Сбросить",
            bg="#808080",  # Серый цвет для кнопки сброса
            fg="white",
            command=self.reset_to_defaults,
            width=15,
            height=2,
            font=("Arial", 10),
            relief=tk.RAISED,
            bd=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка Отмена
        cancel_btn = tk.Button(
            buttons_frame,
            text="Отмена",
            bg="#808080",  # Серый цвет для кнопки отмены
            fg="white",
            command=self.close_window,
            width=15,
            height=2,
            font=("Arial", 10),
            relief=tk.RAISED,
            bd=2
        )
        cancel_btn.pack(side=tk.LEFT)
    
    def get_color_name(self, hex_color):
        """Возвращает читаемое имя цвета"""
        color_names = {
            "#000000": "Черный",
            "#FFFFFF": "Белый",
            "#FF0000": "Красный",
            "#00FF00": "Зеленый",
            "#0000FF": "Синий",
            "#FFFF00": "Желтый",
            "#FF00FF": "Пурпурный",
            "#00FFFF": "Бирюзовый",
            "#808080": "Серый",
            "#FFA500": "Оранжевый",
            "#800080": "Фиолетовый",
            "#008000": "Темно-зеленый",
            "#800000": "Бордовый",
            "#E0E0E0": "Светло-серый",
            "#C0C0C0": "Серебряный",
            "#FFC0CB": "Розовый",
            "#8B4513": "Коричневый"
        }
        
        return color_names.get(hex_color.upper(), hex_color)
    
    def is_dark_color(self, hex_color):
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:  # Короткий формат #FFF
                hex_color = ''.join(c*2 for c in hex_color)
            
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Вычисляем яркость
            brightness = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
            return brightness < 0.5
        except:
            return True
    
    def choose_button_color(self):
        color = colorchooser.askcolor(
            initialcolor=self.settings['button_color'],
            title="Выберите цвет кнопок"
        )
        
        if color[1]:  # Если цвет выбран
            self.settings['button_color'] = color[1]
            self.button_color_btn.config(
                text=self.get_color_name(color[1]),
                bg=color[1],
                fg="#FFFFFF" if self.is_dark_color(color[1]) else "#000000"
            )
    
    def choose_text_color(self):
        color = colorchooser.askcolor(
            initialcolor=self.settings['text_color'],
            title="Выберите цвет текста"
        )
        
        if color[1]:  # Если цвет выбран
            self.settings['text_color'] = color[1]
            self.text_color_btn.config(
                text=self.get_color_name(color[1]),
                bg=color[1],
                fg="#FFFFFF" if self.is_dark_color(color[1]) else "#000000"
            )
            # Обновляем цвет текста в окне настроек
            self.update_settings_window_colors()
    
    def choose_background_color(self):
        color = colorchooser.askcolor(
            initialcolor=self.settings['background_color'],
            title="Выберите цвет заднего плана"
        )
        
        if color[1]:  # Если цвет выбран
            self.settings['background_color'] = color[1]
            self.background_color_btn.config(
                text=self.get_color_name(color[1]),
                bg=color[1],
                fg="#FFFFFF" if self.is_dark_color(color[1]) else "#000000"
            )
            # Обновляем фон окна настроек
            self.update_settings_window_colors()
    
    def update_settings_window_colors(self):
        bg_color = self.settings.get('background_color', '#FFFFFF')
        text_color = self.settings.get('text_color', '#000000')
        
        # Обновляем фон окна
        self.window.configure(bg=bg_color)
        
        # Обновляем все Frame
        for widget in self.window.winfo_children():
            self.update_widget_colors(widget, bg_color, text_color)
    
    def update_widget_colors(self, widget, bg_color, text_color):
        if isinstance(widget, tk.Frame):
            widget.configure(bg=bg_color)
        elif isinstance(widget, tk.Label):
            widget.configure(bg=bg_color, fg=text_color)
        elif isinstance(widget, tk.LabelFrame):
            widget.configure(bg=bg_color, fg=text_color)
        
        # Рекурсивно обходим дочерние виджеты
        for child in widget.winfo_children():
            self.update_widget_colors(child, bg_color, text_color)
    
    def save_and_apply_settings(self):
        # Обновляем настройки в памяти
        self.settings['font_family'] = self.selected_font.get()

        # График прогноза мог быть изменён в окне ML после открытия настроек — не затирать
        if isinstance(self.state.settings.get("forecast_settings"), dict):
            self.settings["forecast_settings"] = copy.deepcopy(
                self.state.settings["forecast_settings"]
            )

        # Сохраняем в глобальное состояние
        self.state.settings = copy.deepcopy(self.settings)
        self.state.save_settings()
        
        # Вызываем коллбэк если есть
        if self.on_save_callback:
            self.on_save_callback(self.settings)
    
        self.close_window()
    
    def reset_to_defaults(self):
        """Сброс настроек к значениям по умолчанию"""
        if messagebox.askyesno(
            "Сброс настроек",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?\n\n"
            "Все текущие настройки будут утеряны."
        ):
            # Получаем настройки по умолчанию
            default_settings = self.state.get_default_settings()
            
            # Обновляем текущие настройки
            self.settings = default_settings.copy()
            
            # Обновляем UI
            self.selected_font.set(self.settings['font_family'])
            
            # Обновляем кнопки цветов
            self.button_color_btn.config(
                text=self.get_color_name(self.settings['button_color']),
                bg=self.settings['button_color'],
                fg="#bec0c2" if self.is_dark_color(self.settings['button_color']) else "#bec0c2"
            )
            
            self.text_color_btn.config(
                text=self.get_color_name(self.settings['text_color']),
                bg=self.settings['text_color'],
                fg="#000000" if self.is_dark_color(self.settings['text_color']) else "#000000"
            )
            
            self.background_color_btn.config(
                text=self.get_color_name(self.settings['background_color']),
                bg=self.settings['background_color'],
                fg="#ff8080" if self.is_dark_color(self.settings['background_color']) else "#ff8080"
            )
            
            # Обновляем окно настроек
            self.update_settings_window_colors()
            
            messagebox.showinfo(
                "Сброс настроек",
                "Настройки сброшены к значениям по умолчанию."
            )
    
    def press_key(self, event):
        """Обработка нажатия клавиш"""
        if event.keysym == 'Escape' or event.char == '\x1b':
            self.close_window()
        elif event.keysym == 's' and event.state & 4:  # Ctrl+S
            self.save_and_apply_settings()
        elif event.keysym == 'r' and event.state & 4:  # Ctrl+R
            self.reset_to_defaults()
    
    def close_window(self):
        """Закрытие окна с проверкой несохраненных изменений"""
        # Проверяем, были ли изменения
        current_values = {
            'font_family': self.selected_font.get(),
            'button_color': self.settings['button_color'],
            'text_color': self.settings['text_color'],
            'background_color': self.settings['background_color']
        }
        
        # Сравниваем с изначальными настройками
        original = self.state.settings
        
        if (current_values['font_family'] != original['font_family'] or
            current_values['button_color'] != original['button_color'] or
            current_values['text_color'] != original['text_color'] or
            current_values['background_color'] != original['background_color']):
            
            response = messagebox.askyesnocancel(
                "Несохраненные изменения",
                "У вас есть несохраненные изменения. Сохранить перед закрытием?"
            )
            
            if response is None:  # Отмена
                return
            elif response:  # Да (Сохранить)
                self.save_and_apply_settings()
                return
        
        self.window.destroy()