"""
Модуль для выполнения запросов к базе данных operations.db
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class SalesAnalyzer:
    def __init__(self, db_path="Databases/operations.db"):
        self.db_path = Path(db_path)
        
    def get_connection(self):
        """Создает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_sales_by_date_range(self, start_date, end_date):
        """
        Получает продажи за указанный период
        
        Args:
            start_date (str): Дата начала в формате 'YYYY-MM-DD'
            end_date (str): Дата окончания в формате 'YYYY-MM-DD'
            
        Returns:
            list: Список продаж с деталями
        """
        query = """
        SELECT 
            s.sale_id,
            s.created_at,
            s.account,
            s.total_amount,
            si.item_name,
            si.category,
            si.price
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        ORDER BY s.created_at
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()
    
    def get_daily_sales_summary(self, start_date, end_date):
        """
        Сумма продаж по дням
        
        Returns:
            dict: {дата: общая_сумма}
        """
        query = """
        SELECT 
            DATE(created_at) as sale_date,
            SUM(total_amount) as daily_total
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY sale_date
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['sale_date']] = row['daily_total']
            return results
    
    def get_item_sales_summary(self, start_date, end_date):
        """
        Сумма продаж по товарам
        
        Returns:
            dict: {товар: сумма}
        """
        query = """
        SELECT 
            si.item_name,
            SUM(si.price) as item_total,
            COUNT(*) as item_count
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY si.item_name
        ORDER BY item_total DESC
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['item_name']] = {
                    'total': row['item_total'],
                    'count': row['item_count']
                }
            return results
    
    def get_category_sales_summary(self, start_date, end_date):
        """
        Сумма продаж по категориям товаров
        
        Returns:
            dict: {категория: сумма}
        """
        query = """
        SELECT 
            si.category,
            SUM(si.price) as category_total,
            COUNT(*) as category_count
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY si.category
        ORDER BY category_total DESC
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['category']] = {
                    'total': row['category_total'],
                    'count': row['category_count']
                }
            return results

    def get_distinct_items(self):
        """Список уникальных наименований товаров из продаж."""
        query = """
        SELECT DISTINCT item_name FROM sales_items
        WHERE item_name IS NOT NULL AND TRIM(item_name) != ''
        ORDER BY item_name
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [row['item_name'] for row in cursor.fetchall()]

    def get_distinct_categories(self):
        """Список уникальных категорий из продаж. Пустые/NULL отображаются как «(Без категории)»."""
        query = """
        SELECT DISTINCT category FROM sales_items
        ORDER BY category
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            seen = set()
            result = []
            for row in cursor.fetchall():
                raw = row['category']
                if raw is None or (isinstance(raw, str) and raw.strip() == ''):
                    display = '(Без категории)'
                else:
                    display = raw
                if display not in seen:
                    seen.add(display)
                    result.append(display)
            return result

    def get_sales_by_items_daily(self, item_names, start_date, end_date):
        """
        Продажи по выбранным товарам: разбивка по дням и итоги.
        item_names: список названий товаров (или один товар).
        Returns:
            daily: dict {date_str: {'total': сумма, 'count': кол-во проданных единиц}}
            total_count: общее кол-во проданных единиц
            total_revenue: общая выручка
        """
        if not item_names:
            return {}, 0, 0
        names = list(item_names) if isinstance(item_names, (list, tuple)) else [item_names]
        placeholders = ','.join(['?'] * len(names))
        query_daily = f"""
        SELECT 
            DATE(s.created_at) as sale_date,
            SUM(si.price) as day_total,
            COUNT(*) as day_count
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        AND si.item_name IN ({placeholders})
        GROUP BY DATE(s.created_at)
        ORDER BY sale_date
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_daily, [start_date, end_date] + names)
            daily = {}
            total_count = 0
            total_revenue = 0
            for row in cursor.fetchall():
                daily[row['sale_date']] = {'total': row['day_total'], 'count': row['day_count']}
                total_count += row['day_count']
                total_revenue += row['day_total']
            return daily, total_count, total_revenue

    def get_sales_by_categories_daily(self, category_names, start_date, end_date):
        """
        Продажи по выбранным категориям: разбивка по дням и итоги.
        category_names: список категорий (или одна). «(Без категории)» = NULL или пустая строка.
        Returns:
            daily, total_count, total_revenue (аналогично get_sales_by_items_daily).
        """
        if not category_names:
            return {}, 0, 0
        names = list(category_names) if isinstance(category_names, (list, tuple)) else [category_names]
        no_cat = '(Без категории)'
        normal = [n for n in names if n != no_cat]
        has_no_cat = no_cat in names

        if has_no_cat and not normal:
            condition = "(si.category IS NULL OR TRIM(COALESCE(si.category, '')) = '')"
            params = [start_date, end_date]
        elif has_no_cat and normal:
            placeholders = ','.join(['?'] * len(normal))
            condition = f"((si.category IS NULL OR TRIM(COALESCE(si.category, '')) = '') OR si.category IN ({placeholders}))"
            params = [start_date, end_date] + normal
        else:
            placeholders = ','.join(['?'] * len(normal))
            condition = f"si.category IN ({placeholders})"
            params = [start_date, end_date] + normal

        query_daily = f"""
        SELECT 
            DATE(s.created_at) as sale_date,
            SUM(si.price) as day_total,
            COUNT(*) as day_count
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        AND {condition}
        GROUP BY DATE(s.created_at)
        ORDER BY sale_date
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_daily, params)
            daily = {}
            total_count = 0
            total_revenue = 0
            for row in cursor.fetchall():
                daily[row['sale_date']] = {'total': row['day_total'], 'count': row['day_count']}
                total_count += row['day_count']
                total_revenue += row['day_total']
            return daily, total_count, total_revenue

    def get_account_sales_summary(self, start_date, end_date):
        """
        Сумма продаж по аккаунтам
        
        Returns:
            dict: {аккаунт: {total: сумма, count: количество, avg: средняя сумма}}
        """
        query = """
        SELECT 
            account,
            SUM(total_amount) as account_total,
            COUNT(*) as account_count,
            AVG(total_amount) as account_avg
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account
        ORDER BY account_total DESC
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['account']] = {
                    'total': row['account_total'],
                    'count': row['account_count'],
                    'avg': row['account_avg']
                }
            return results
    
    def get_account_detailed_sales(self, start_date, end_date):
        """
        Детальные продажи по аккаунтам с группировкой по месяцам/годам
        
        Returns:
            dict: {аккаунт: {год-месяц: сумма}}
        """
        query = """
        SELECT 
            account,
            strftime('%Y-%m', created_at) as year_month,
            SUM(total_amount) as month_total,
            COUNT(*) as transaction_count
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account, strftime('%Y-%m', created_at)
        ORDER BY account, year_month
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                account = row['account']
                year_month = row['year_month']
                
                if account not in results:
                    results[account] = {}
                
                results[account][year_month] = {
                    'total': row['month_total'],
                    'count': row['transaction_count']
                }
            return results
    
    def get_monthly_sales_timeline(self, start_date, end_date):
        """
        Получает временную шкалу продаж с группировкой по месяцам
        
        Returns:
            dict: {год-месяц: {total: сумма, account_count: количество аккаунтов, 
                              transaction_count: количество транзакций}}
        """
        query = """
        SELECT 
            strftime('%Y-%m', created_at) as year_month,
            SUM(total_amount) as month_total,
            COUNT(DISTINCT account) as account_count,
            COUNT(*) as transaction_count
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY year_month
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['year_month']] = {
                    'total': row['month_total'],
                    'account_count': row['account_count'],
                    'transaction_count': row['transaction_count']
                }
            return results

    def get_hourly_sales_totals(self, start_date, end_date):
        """
        Суммы продаж по календарной дате и часу (0–23) по полю created_at.

        Returns:
            list[dict]: каждый элемент — calendar_date (YYYY-MM-DD), hour (int), total (float)
        """
        query = """
        SELECT
            DATE(created_at) AS calendar_date,
            CAST(strftime('%H', created_at) AS INTEGER) AS hour,
            SUM(total_amount) AS hourly_total
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at), CAST(strftime('%H', created_at) AS INTEGER)
        ORDER BY calendar_date, hour
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            return [
                {
                    "calendar_date": row["calendar_date"],
                    "hour": int(row["hour"]),
                    "total": float(row["hourly_total"] or 0),
                }
                for row in cursor.fetchall()
            ]

    def get_daily_item_sales_units(self, start_date, end_date):
        """
        Число проданных единиц по товару и календарному дню (каждая строка sales_items = 1 единица).

        Returns:
            list[dict]: calendar_date (YYYY-MM-DD), item_name, units (int)
        """
        query = """
        SELECT
            DATE(s.created_at) AS calendar_date,
            si.item_name AS item_name,
            COUNT(*) AS units
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
          AND si.item_name IS NOT NULL AND TRIM(si.item_name) != ''
        GROUP BY DATE(s.created_at), si.item_name
        ORDER BY calendar_date, item_name
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            return [
                {
                    "calendar_date": row["calendar_date"],
                    "item_name": row["item_name"],
                    "units": int(row["units"] or 0),
                }
                for row in cursor.fetchall()
            ]

    def get_account_monthly_breakdown(self, start_date, end_date, top_n=10):
        """
        Получает детализацию по месяцам для топ-N аккаунтов
        
        Returns:
            dict: {аккаунт: {год-месяц: сумма}}
        """
        # Сначала получаем топ-N аккаунтов по общей сумме
        top_accounts_query = """
        SELECT account, SUM(total_amount) as total
        FROM sales
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account
        ORDER BY total DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(top_accounts_query, (start_date, end_date, top_n))
            top_accounts = [row['account'] for row in cursor.fetchall()]
            
            if not top_accounts:
                return {}
            
            # Получаем детализацию для топ-аккаунтов
            placeholders = ','.join(['?'] * len(top_accounts))
            details_query = f"""
            SELECT 
                account,
                strftime('%Y-%m', created_at) as year_month,
                SUM(total_amount) as month_total
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ?
            AND account IN ({placeholders})
            GROUP BY account, strftime('%Y-%m', created_at)
            ORDER BY account, year_month
            """
            
            params = [start_date, end_date] + top_accounts
            cursor.execute(details_query, params)
            
            results = {}
            for row in cursor.fetchall():
                account = row['account']
                year_month = row['year_month']
                
                if account not in results:
                    results[account] = {}
                
                results[account][year_month] = row['month_total']
            
            return results
    
    def get_account_performance_metrics(self, start_date, end_date):
        """
        Получает метрики производительности аккаунтов
        
        Returns:
            list: Список словарей с метриками для каждого аккаунта
        """
        query = """
        WITH account_stats AS (
            SELECT 
                account,
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_amount,
                AVG(total_amount) as avg_transaction,
                MIN(created_at) as first_transaction,
                MAX(created_at) as last_transaction,
                COUNT(DISTINCT strftime('%Y-%m', created_at)) as active_months
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY account
        )
        SELECT 
            account,
            transaction_count,
            total_amount,
            avg_transaction,
            first_transaction,
            last_transaction,
            active_months,
            CASE 
                WHEN active_months > 0 
                THEN ROUND(total_amount / active_months, 2)
                ELSE 0 
            END as monthly_avg
        FROM account_stats
        ORDER BY total_amount DESC
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            
            results = []
            for row in cursor.fetchall():
                # Рассчитываем дополнительные метрики
                days_active = 0
                if row['first_transaction'] and row['last_transaction']:
                    try:
                        first_dt = datetime.strptime(row['first_transaction'], '%Y-%m-%d %H:%M:%S')
                        last_dt = datetime.strptime(row['last_transaction'], '%Y-%m-%d %H:%M:%S')
                        days_active = (last_dt - first_dt).days + 1
                    except:
                        pass
                
                results.append({
                    'account': row['account'],
                    'transaction_count': row['transaction_count'],
                    'total_amount': row['total_amount'],
                    'avg_transaction': row['avg_transaction'],
                    'monthly_avg': row['monthly_avg'],
                    'first_transaction': row['first_transaction'],
                    'last_transaction': row['last_transaction'],
                    'active_months': row['active_months'],
                    'days_active': days_active,
                    'daily_avg': row['total_amount'] / days_active if days_active > 0 else 0
                })
            
            return results
    
    def get_account_comparison_data(self, start_date, end_date):
        """
        Получает данные для сравнения аккаунтов
        
        Returns:
            dict: Словарь с данными для визуализации сравнения
        """
        # Получаем топ-10 аккаунтов
        top_accounts = self.get_account_sales_summary(start_date, end_date)
        top_10_accounts = dict(sorted(top_accounts.items(), 
                                    key=lambda x: x[1]['total'], 
                                    reverse=True)[:10])
        
        # Получаем месячную разбивку для топ-аккаунтов
        monthly_data = self.get_account_monthly_breakdown(start_date, end_date, 10)
        
        # Собираем все уникальные месяцы
        all_months = set()
        for account_data in monthly_data.values():
            all_months.update(account_data.keys())
        
        all_months = sorted(list(all_months))
        
        return {
            'top_accounts': top_10_accounts,
            'monthly_data': monthly_data,
            'all_months': all_months,
            'total_period_sales': sum(acc['total'] for acc in top_accounts.values()),
            'account_count': len(top_accounts)
        }
    
    def get_date_range_stats(self):
        """
        Получает минимальную и максимальную даты в базе данных
        
        Returns:
            tuple: (min_date, max_date) в формате 'YYYY-MM-DD'
        """
        query = """
        SELECT 
            MIN(DATE(created_at)) as min_date,
            MAX(DATE(created_at)) as max_date
        FROM sales
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return row['min_date'], row['max_date']
    
    def format_date_for_display(self, date_str):
        """Форматирует дату из БД в DD-MM-YYYY"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d-%m-%Y')
        except:
            pass
        return date_str
    
    def format_date_for_db(self, date_str):
        """Форматирует дату из DD-MM-YYYY в YYYY-MM-DD"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        return date_str
    
    def format_year_month(self, year_month_str):
        """Форматирует YYYY-MM в русский формат (Янв 2023)"""
        try:
            dt = datetime.strptime(year_month_str, '%Y-%m')
            month_names = [
                'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'
            ]
            return f"{month_names[dt.month-1]} {dt.year}"
        except:
            return year_month_str


class BuyingsAnalyzer:
    """Анализатор закупок (таблицы buyings, buyings_items)."""
    def __init__(self, db_path="Databases/operations.db"):
        self.db_path = Path(db_path)

    def get_connection(self):
        """Создает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_distinct_items(self):
        """Список уникальных наименований товаров из закупок (buyings_items)."""
        query = """
        SELECT DISTINCT item_name FROM buyings_items
        WHERE item_name IS NOT NULL AND TRIM(item_name) != ''
        ORDER BY item_name
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [row['item_name'] for row in cursor.fetchall()]

    def get_distinct_categories(self):
        """Список уникальных категорий из закупок. Пустые/NULL — «(Без категории)»."""
        query = """
        SELECT DISTINCT category FROM buyings_items
        ORDER BY category
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            seen = set()
            result = []
            for row in cursor.fetchall():
                raw = row['category']
                if raw is None or (isinstance(raw, str) and raw.strip() == ''):
                    display = '(Без категории)'
                else:
                    display = raw
                if display not in seen:
                    seen.add(display)
                    result.append(display)
            return result

    def get_buyings_by_items_daily(self, item_names, start_date, end_date):
        """
        Закупки по выбранным товарам: разбивка по дням и итоги.
        Returns: daily, total_count, total_revenue (сумма закупок).
        """
        if not item_names:
            return {}, 0, 0
        names = list(item_names) if isinstance(item_names, (list, tuple)) else [item_names]
        placeholders = ','.join(['?'] * len(names))
        query_daily = f"""
        SELECT 
            DATE(b.created_at) as buy_date,
            SUM(bi.price) as day_total,
            COUNT(*) as day_count
        FROM buyings b
        JOIN buyings_items bi ON b.buy_id = bi.buy_id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        AND bi.item_name IN ({placeholders})
        GROUP BY DATE(b.created_at)
        ORDER BY buy_date
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_daily, [start_date, end_date] + names)
            daily = {}
            total_count = 0
            total_revenue = 0
            for row in cursor.fetchall():
                daily[row['buy_date']] = {'total': row['day_total'], 'count': row['day_count']}
                total_count += row['day_count']
                total_revenue += row['day_total']
            return daily, total_count, total_revenue

    def get_buyings_by_categories_daily(self, category_names, start_date, end_date):
        """
        Закупки по выбранным категориям: разбивка по дням и итоги.
        «(Без категории)» = NULL или пустая строка.
        Returns: daily, total_count, total_revenue.
        """
        if not category_names:
            return {}, 0, 0
        names = list(category_names) if isinstance(category_names, (list, tuple)) else [category_names]
        no_cat = '(Без категории)'
        normal = [n for n in names if n != no_cat]
        has_no_cat = no_cat in names

        if has_no_cat and not normal:
            condition = "(bi.category IS NULL OR TRIM(COALESCE(bi.category, '')) = '')"
            params = [start_date, end_date]
        elif has_no_cat and normal:
            placeholders = ','.join(['?'] * len(normal))
            condition = f"((bi.category IS NULL OR TRIM(COALESCE(bi.category, '')) = '') OR bi.category IN ({placeholders}))"
            params = [start_date, end_date] + normal
        else:
            placeholders = ','.join(['?'] * len(normal))
            condition = f"bi.category IN ({placeholders})"
            params = [start_date, end_date] + normal

        query_daily = f"""
        SELECT 
            DATE(b.created_at) as buy_date,
            SUM(bi.price) as day_total,
            COUNT(*) as day_count
        FROM buyings b
        JOIN buyings_items bi ON b.buy_id = bi.buy_id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        AND {condition}
        GROUP BY DATE(b.created_at)
        ORDER BY buy_date
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_daily, params)
            daily = {}
            total_count = 0
            total_revenue = 0
            for row in cursor.fetchall():
                daily[row['buy_date']] = {'total': row['day_total'], 'count': row['day_count']}
                total_count += row['day_count']
                total_revenue += row['day_total']
            return daily, total_count, total_revenue

    def get_daily_buyings_summary(self, start_date, end_date):
        """
        Сумма закупок по дням.
        Returns:
            dict: {дата: общая_сумма}
        """
        query = """
        SELECT 
            DATE(created_at) as buy_date,
            SUM(total_amount) as daily_total
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY buy_date
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['buy_date']] = row['daily_total']
            return results

    def get_item_buyings_summary(self, start_date, end_date):
        """
        Сумма закупок по товарам (из buyings_items).
        Returns:
            dict: {товар: {total, count}}
        """
        query = """
        SELECT 
            bi.item_name,
            SUM(bi.price) as item_total,
            COUNT(*) as item_count
        FROM buyings b
        JOIN buyings_items bi ON b.buy_id = bi.buy_id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        GROUP BY bi.item_name
        ORDER BY item_total DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['item_name']] = {
                    'total': row['item_total'],
                    'count': row['item_count']
                }
            return results

    def get_category_buyings_summary(self, start_date, end_date):
        """
        Сумма закупок по категориям товаров.
        Returns:
            dict: {категория: {total, count}}
        """
        query = """
        SELECT 
            bi.category,
            SUM(bi.price) as category_total,
            COUNT(*) as category_count
        FROM buyings b
        JOIN buyings_items bi ON b.buy_id = bi.buy_id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        GROUP BY bi.category
        ORDER BY category_total DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['category']] = {
                    'total': row['category_total'],
                    'count': row['category_count']
                }
            return results

    def get_account_buyings_summary(self, start_date, end_date):
        """
        Сумма закупок по аккаунтам.
        Returns:
            dict: {аккаунт: {total: сумма, count: количество, avg: средняя сумма}}
        """
        query = """
        SELECT 
            account,
            SUM(total_amount) as account_total,
            COUNT(*) as account_count,
            AVG(total_amount) as account_avg
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account
        ORDER BY account_total DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['account']] = {
                    'total': row['account_total'],
                    'count': row['account_count'],
                    'avg': row['account_avg']
                }
            return results

    def get_account_detailed_buyings(self, start_date, end_date):
        """
        Детальные закупки по аккаунтам с группировкой по месяцам/годам.
        Returns:
            dict: {аккаунт: {год-месяц: {total, transaction_count}}}
        """
        query = """
        SELECT 
            account,
            strftime('%Y-%m', created_at) as year_month,
            SUM(total_amount) as month_total,
            COUNT(*) as transaction_count
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account, strftime('%Y-%m', created_at)
        ORDER BY account, year_month
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                account = row['account']
                year_month = row['year_month']
                if account not in results:
                    results[account] = {}
                results[account][year_month] = {
                    'total': row['month_total'],
                    'count': row['transaction_count']
                }
            return results

    def get_monthly_buyings_timeline(self, start_date, end_date):
        """
        Временная шкала закупок по месяцам.
        Returns:
            dict: {год-месяц: {total, account_count, transaction_count}}
        """
        query = """
        SELECT 
            strftime('%Y-%m', created_at) as year_month,
            SUM(total_amount) as month_total,
            COUNT(DISTINCT account) as account_count,
            COUNT(*) as transaction_count
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY year_month
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = {}
            for row in cursor.fetchall():
                results[row['year_month']] = {
                    'total': row['month_total'],
                    'account_count': row['account_count'],
                    'transaction_count': row['transaction_count']
                }
            return results

    def get_hourly_buyings_totals(self, start_date, end_date):
        """
        Суммы закупок по календарной дате и часу (0–23) по created_at.

        Returns:
            list[dict]: calendar_date, hour, total
        """
        query = """
        SELECT
            DATE(created_at) AS calendar_date,
            CAST(strftime('%H', created_at) AS INTEGER) AS hour,
            SUM(total_amount) AS hourly_total
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at), CAST(strftime('%H', created_at) AS INTEGER)
        ORDER BY calendar_date, hour
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            return [
                {
                    "calendar_date": row["calendar_date"],
                    "hour": int(row["hour"]),
                    "total": float(row["hourly_total"] or 0),
                }
                for row in cursor.fetchall()
            ]

    def get_account_monthly_breakdown(self, start_date, end_date, top_n=10):
        """
        Детализация по месяцам для топ-N аккаунтов по закупкам.
        Returns:
            dict: {аккаунт: {год-месяц: сумма}}
        """
        top_accounts_query = """
        SELECT account, SUM(total_amount) as total
        FROM buyings
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY account
        ORDER BY total DESC
        LIMIT ?
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(top_accounts_query, (start_date, end_date, top_n))
            top_accounts = [row['account'] for row in cursor.fetchall()]
            if not top_accounts:
                return {}
            placeholders = ','.join(['?'] * len(top_accounts))
            details_query = f"""
            SELECT 
                account,
                strftime('%Y-%m', created_at) as year_month,
                SUM(total_amount) as month_total
            FROM buyings
            WHERE DATE(created_at) BETWEEN ? AND ?
            AND account IN ({placeholders})
            GROUP BY account, strftime('%Y-%m', created_at)
            ORDER BY account, year_month
            """
            params = [start_date, end_date] + top_accounts
            cursor.execute(details_query, params)
            results = {}
            for row in cursor.fetchall():
                account = row['account']
                year_month = row['year_month']
                if account not in results:
                    results[account] = {}
                results[account][year_month] = row['month_total']
            return results

    def get_account_performance_metrics(self, start_date, end_date):
        """
        Метрики по аккаунтам для закупок.
        Returns:
            list: Список словарей с метриками для каждого аккаунта
        """
        query = """
        WITH account_stats AS (
            SELECT 
                account,
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_amount,
                AVG(total_amount) as avg_transaction,
                MIN(created_at) as first_transaction,
                MAX(created_at) as last_transaction,
                COUNT(DISTINCT strftime('%Y-%m', created_at)) as active_months
            FROM buyings
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY account
        )
        SELECT 
            account,
            transaction_count,
            total_amount,
            avg_transaction,
            first_transaction,
            last_transaction,
            active_months,
            CASE 
                WHEN active_months > 0 
                THEN ROUND(total_amount / active_months, 2)
                ELSE 0 
            END as monthly_avg
        FROM account_stats
        ORDER BY total_amount DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            results = []
            for row in cursor.fetchall():
                days_active = 0
                if row['first_transaction'] and row['last_transaction']:
                    try:
                        first_dt = datetime.strptime(row['first_transaction'], '%Y-%m-%d %H:%M:%S')
                        last_dt = datetime.strptime(row['last_transaction'], '%Y-%m-%d %H:%M:%S')
                        days_active = (last_dt - first_dt).days + 1
                    except Exception:
                        try:
                            first_dt = datetime.strptime(row['first_transaction'], '%Y-%m-%d')
                            last_dt = datetime.strptime(row['last_transaction'], '%Y-%m-%d')
                            days_active = (last_dt - first_dt).days + 1
                        except Exception:
                            pass
                results.append({
                    'account': row['account'],
                    'transaction_count': row['transaction_count'],
                    'total_amount': row['total_amount'],
                    'avg_transaction': row['avg_transaction'],
                    'monthly_avg': row['monthly_avg'],
                    'first_transaction': row['first_transaction'],
                    'last_transaction': row['last_transaction'],
                    'active_months': row['active_months'],
                    'days_active': days_active,
                    'daily_avg': row['total_amount'] / days_active if days_active > 0 else 0
                })
            return results

    def get_account_comparison_data(self, start_date, end_date):
        """
        Данные для сравнения аккаунтов по закупкам.
        Returns:
            dict: top_accounts, monthly_data, all_months, total_period_sales, account_count
        """
        top_accounts = self.get_account_buyings_summary(start_date, end_date)
        top_10_accounts = dict(sorted(top_accounts.items(),
                                     key=lambda x: x[1]['total'],
                                     reverse=True)[:10])
        monthly_data = self.get_account_monthly_breakdown(start_date, end_date, 10)
        all_months = set()
        for account_data in monthly_data.values():
            all_months.update(account_data.keys())
        all_months = sorted(list(all_months))
        return {
            'top_accounts': top_10_accounts,
            'monthly_data': monthly_data,
            'all_months': all_months,
            'total_period_sales': sum(acc['total'] for acc in top_accounts.values()),
            'account_count': len(top_accounts)
        }

    def get_date_range_stats(self):
        """
        Минимальная и максимальная даты закупок в БД.
        Returns:
            tuple: (min_date, max_date) в формате 'YYYY-MM-DD'
        """
        query = """
        SELECT 
            MIN(DATE(created_at)) as min_date,
            MAX(DATE(created_at)) as max_date
        FROM buyings
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return row['min_date'], row['max_date']

    def format_date_for_display(self, date_str):
        """Форматирует дату из БД в DD-MM-YYYY"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d-%m-%Y')
        except Exception:
            pass
        return date_str

    def format_date_for_db(self, date_str):
        """Форматирует дату из DD-MM-YYYY в YYYY-MM-DD"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        return date_str

    def format_year_month(self, year_month_str):
        """Форматирует YYYY-MM в русский формат (Янв 2023)"""
        try:
            dt = datetime.strptime(year_month_str, '%Y-%m')
            month_names = [
                'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'
            ]
            return f"{month_names[dt.month-1]} {dt.year}"
        except Exception:
            return year_month_str


def get_item_margin_ranking(start_date, end_date, db_path="Databases/operations.db"):
    """
    Сводка по товарам: выручка (сумма price в продажах) минус закупки (сумма price в закупках)
    за период, сопоставление по item_name.

    Returns:
        list[dict]: поля item_name, sales_total, buy_total, margin, sale_lines, buy_lines, status
        status: 'both' | 'sales_only' | 'buy_only'
    """
    path = Path(db_path)
    sales_q = """
        SELECT si.item_name AS item_name,
               SUM(si.price) AS revenue,
               COUNT(*) AS lines_cnt
        FROM sales s
        JOIN sales_items si ON s.sale_id = si.sale_id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
          AND si.item_name IS NOT NULL AND TRIM(si.item_name) != ''
        GROUP BY si.item_name
    """
    buy_q = """
        SELECT bi.item_name AS item_name,
               SUM(bi.price) AS spent,
               COUNT(*) AS lines_cnt
        FROM buyings b
        JOIN buyings_items bi ON b.buy_id = bi.buy_id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
          AND bi.item_name IS NOT NULL AND TRIM(bi.item_name) != ''
        GROUP BY bi.item_name
    """
    sales_map = {}
    buy_map = {}
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sales_q, (start_date, end_date))
        for row in cur.fetchall():
            sales_map[row['item_name']] = {
                'total': float(row['revenue'] or 0),
                'lines': int(row['lines_cnt'] or 0),
            }
        cur.execute(buy_q, (start_date, end_date))
        for row in cur.fetchall():
            buy_map[row['item_name']] = {
                'total': float(row['spent'] or 0),
                'lines': int(row['lines_cnt'] or 0),
            }

    names = set(sales_map.keys()) | set(buy_map.keys())
    rows = []
    for name in names:
        st = sales_map.get(name, {'total': 0.0, 'lines': 0})
        bt = buy_map.get(name, {'total': 0.0, 'lines': 0})
        sales_total = st['total']
        buy_total = bt['total']
        margin = sales_total - buy_total
        if sales_total > 0 and buy_total > 0:
            status = 'both'
        elif sales_total > 0:
            status = 'sales_only'
        else:
            status = 'buy_only'
        rows.append({
            'item_name': name,
            'sales_total': sales_total,
            'buy_total': buy_total,
            'margin': margin,
            'sale_lines': st['lines'],
            'buy_lines': bt['lines'],
            'status': status,
        })
    rows.sort(key=lambda r: r['margin'], reverse=True)
    return rows