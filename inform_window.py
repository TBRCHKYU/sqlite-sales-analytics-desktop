import tkinter as tk
from tkinter import ttk, messagebox

from app_state import app_state
from window_geometry import place_geometry
from sales_analysis_window import SalesAnalysisWindow
from sales_accounts_window import AccountsAnalysisWindow
from buy_accounts_window import BuyingsAnalysisWindow
from buy_analysis_window import BuyingsAnalysisByDateWindow
from sales_by_item_window import SalesByItemWindow
from buy_by_item_window import BuyingsByItemWindow
from item_margin_window import ItemMarginWindow
from hourly_forecast_window import HourlyForecastWindow
from stock_recommendation_window import StockRecommendationWindow


class inform_window:
    def __init__(self, parent):
        self.parent = parent
        self.state = app_state
        self.window = tk.Toplevel(parent)
        self.window.transient(parent)
        place_geometry(self.window, 820, 620)

        self.settings = self.state.settings.copy()
        self.button_color = self.settings.get("button_color", "#000000")
        self.text_color = self.settings.get("text_color", "#FFFFFF")
        self.background_color = self.settings.get("background_color", "#FFFFFF")
        self.font_family = self.settings.get("font_family", "Arial")
        self.font_size = self.settings.get("font_size", 12)

        self.window.configure(bg=self.background_color)
        self.apply_settings_on_startup()
        self.create_custom_styles()
        self.create_widgets()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def apply_settings_on_startup(self):
        from styles import apply_theme
        settings = self.state.settings
        self.window.configure(bg=settings.get("background_color", "#FFFFFF"))
        self.style = ttk.Style()
        apply_theme(self.style, settings)

    def create_custom_styles(self):
        pass

    def create_widgets(self):
        self.window.title("Отчёты и аналитика")

        header = ttk.Frame(self.window, style="Custom.TFrame")
        header.pack(fill=tk.X, padx=12, pady=(12, 4))
        ttk.Label(
            header,
            text="Исторические отчёты, прогноз по тренду и рейтинг маржи по товарам.",
            style="Hint.TLabel",
            wraplength=780,
        ).pack(anchor=tk.W)

        notebook = ttk.Notebook(self.window, style="Custom.TFrame")
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tab_sales = ttk.Frame(notebook, style="Custom.TFrame")
        notebook.add(tab_sales, text="Детализация продаж")
        self._fill_sales_tab(tab_sales)

        tab_buy = ttk.Frame(notebook, style="Custom.TFrame")
        notebook.add(tab_buy, text="Детализация закупок")
        self._fill_buy_tab(tab_buy)

        tab_fore = ttk.Frame(notebook, style="Custom.TFrame")
        notebook.add(tab_fore, text="Прогнозы")
        self._fill_forecast_tab(tab_fore)

        tab_margin = ttk.Frame(notebook, style="Custom.TFrame")
        notebook.add(tab_margin, text="Выгодность товаров")
        self._fill_margin_tab(tab_margin)

        ttk.Button(
            self.window,
            text="Закрыть",
            command=self.close_window,
            style="MyButton.TButton",
        ).pack(pady=10)

    def _report_button(self, parent, title, subtitle, command):
        box = ttk.Frame(parent, style="Custom.TFrame")
        box.pack(fill=tk.X, padx=16, pady=6)
        ttk.Button(
            box,
            text=title,
            width=42,
            command=command,
            style="MyButton.TButton",
        ).pack(anchor=tk.W)
        if subtitle:
            ttk.Label(box, text=subtitle, style="Hint.TLabel", wraplength=760).pack(
                anchor=tk.W, padx=(4, 0), pady=(2, 0)
            )

    def _fill_sales_tab(self, parent):
        self._report_button(
            parent,
            "Продажи по датам (график и таблица)",
            "Суммы и динамика по календарным дням за выбранный период.",
            self.open_sales_analysis,
        )
        self._report_button(
            parent,
            "Продажи по аккаунтам",
            "Кто и сколько продал: разрез по учётным аккаунтам.",
            self.open_accounts_analysis,
        )
        self._report_button(
            parent,
            "Продажи по товарам или категориям",
            "Выручка и график по выбранным товарам или категориям.",
            self.open_sales_by_item,
        )

    def _fill_buy_tab(self, parent):
        self._report_button(
            parent,
            "Закупки по датам (график и таблица)",
            "Суммы закупок по дням за период.",
            self.open_buy_analysis_by_date,
        )
        self._report_button(
            parent,
            "Закупки по аккаунтам",
            "Расходы по аккаунтам закупки.",
            self.open_buy_accounts_analysis,
        )
        self._report_button(
            parent,
            "Закупки по товарам или категориям",
            "Суммы и график закупок по товарам/категориям.",
            self.open_buy_by_item,
        )

    def _fill_forecast_tab(self, parent):
        self._report_button(
            parent,
            "ML-прогноз продаж по часам",
            "Почасовые суммы из created_at, учёт графика работы и дня недели; прогноз дня и по часам, метрики на отложенной выборке.",
            self.open_forecast_sales,
        )
        self._report_button(
            parent,
            "Потребность в товаре на день",
            "Список рекомендуемых количеств по наименованиям на выбранную дату: оценка по продажам в тот же день недели за период.",
            self.open_forecast_buyings,
        )

    def _fill_margin_tab(self, parent):
        self._report_button(
            parent,
            "Рейтинг выгодности товаров (маржа)",
            "Для каждого наименования: сумма продаж минус сумма закупок за период. Нужно совпадение имён товара в обеих таблицах.",
            self.open_item_margin,
        )

    def _bind_child_close(self, attr_name: str, child):
        """Сначала destroy окна, затем удаление ссылки — иначе delattr до close ломает закрытие."""

        def handler():
            child.close_window()
            if hasattr(self, attr_name):
                delattr(self, attr_name)

        child.window.protocol("WM_DELETE_WINDOW", handler)

    def open_sales_analysis(self):
        try:
            if hasattr(self, "sales_analysis_window") and self.sales_analysis_window.window.winfo_exists():
                self.sales_analysis_window.window.lift()
                self.sales_analysis_window.window.focus_set()
                return
            self.sales_analysis_window = SalesAnalysisWindow(self.window)
            self._bind_child_close("sales_analysis_window", self.sales_analysis_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно анализа: {e}")

    def open_accounts_analysis(self):
        try:
            if hasattr(self, "sales_accounts_window") and self.sales_accounts_window.window.winfo_exists():
                self.sales_accounts_window.window.lift()
                self.sales_accounts_window.window.focus_set()
                return
            self.sales_accounts_window = AccountsAnalysisWindow(self.window)
            self._bind_child_close("sales_accounts_window", self.sales_accounts_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно анализа по аккаунтам: {e}")

    def open_buy_accounts_analysis(self):
        try:
            if hasattr(self, "buy_accounts_window") and self.buy_accounts_window.window.winfo_exists():
                self.buy_accounts_window.window.lift()
                self.buy_accounts_window.window.focus_set()
                return
            self.buy_accounts_window = BuyingsAnalysisWindow(self.window)
            self._bind_child_close("buy_accounts_window", self.buy_accounts_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно анализа закупок по аккаунтам: {e}")

    def open_buy_analysis_by_date(self):
        try:
            if (
                hasattr(self, "buy_analysis_by_date_window")
                and self.buy_analysis_by_date_window.window.winfo_exists()
            ):
                self.buy_analysis_by_date_window.window.lift()
                self.buy_analysis_by_date_window.window.focus_set()
                return
            self.buy_analysis_by_date_window = BuyingsAnalysisByDateWindow(self.window)
            self._bind_child_close("buy_analysis_by_date_window", self.buy_analysis_by_date_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно анализа закупок по датам: {e}")

    def open_sales_by_item(self):
        try:
            if hasattr(self, "sales_by_item_window") and self.sales_by_item_window.window.winfo_exists():
                self.sales_by_item_window.window.lift()
                self.sales_by_item_window.window.focus_set()
                return
            self.sales_by_item_window = SalesByItemWindow(self.window)
            self._bind_child_close("sales_by_item_window", self.sales_by_item_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно: {e}")

    def open_buy_by_item(self):
        try:
            if hasattr(self, "buy_by_item_window") and self.buy_by_item_window.window.winfo_exists():
                self.buy_by_item_window.window.lift()
                self.buy_by_item_window.window.focus_set()
                return
            self.buy_by_item_window = BuyingsByItemWindow(self.window)
            self._bind_child_close("buy_by_item_window", self.buy_by_item_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно: {e}")

    def open_forecast_sales(self):
        try:
            if hasattr(self, "forecast_sales_window") and self.forecast_sales_window.window.winfo_exists():
                self.forecast_sales_window.window.lift()
                self.forecast_sales_window.window.focus_set()
                return
            self.forecast_sales_window = HourlyForecastWindow(self.window)
            self._bind_child_close("forecast_sales_window", self.forecast_sales_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть прогноз: {e}")

    def open_forecast_buyings(self):
        try:
            if hasattr(self, "forecast_buy_window") and self.forecast_buy_window.window.winfo_exists():
                self.forecast_buy_window.window.lift()
                self.forecast_buy_window.window.focus_set()
                return
            self.forecast_buy_window = StockRecommendationWindow(self.window)
            self._bind_child_close("forecast_buy_window", self.forecast_buy_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть прогноз: {e}")

    def open_item_margin(self):
        try:
            if hasattr(self, "item_margin_window") and self.item_margin_window.window.winfo_exists():
                self.item_margin_window.window.lift()
                self.item_margin_window.window.focus_set()
                return
            self.item_margin_window = ItemMarginWindow(self.window)
            self._bind_child_close("item_margin_window", self.item_margin_window)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть рейтинг: {e}")

    def close_window(self):
        self.window.destroy()
