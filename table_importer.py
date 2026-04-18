import sqlite3
import os
import time
from datetime import datetime
import uuid

def generate_unique_id(prefix="S"):
    """Генерирует уникальный ID с использованием timestamp и случайной части"""
    timestamp = int(time.time() * 1000)  # Используем миллисекунды
    unique_part = str(uuid.uuid4())[:8]  # Берем первые 8 символов UUID
    return f"{prefix}{timestamp}{unique_part}"

def generate_simple_id(prefix="S"):
    """Генерирует ID с инкрементом для избежания коллизий"""
    timestamp = int(time.time())
    # Добавляем микросекунды для уникальности
    microsecond = int(datetime.now().microsecond / 1000)
    return f"{prefix}{timestamp}{microsecond:03d}"

def generate_sequential_id(counter_dict, prefix="S"):
    """Генерирует последовательный ID с счетчиком"""
    timestamp = int(time.time())
    if prefix not in counter_dict:
        counter_dict[prefix] = 0
    counter_dict[prefix] += 1
    return f"{prefix}{timestamp}_{counter_dict[prefix]:04d}"

def get_item_price(items_cursor, item_name):
    """Получает цену товара из базы данных items.db"""
    tables = ['common', 'unusual', 'rare', 'legendary', 'mythical']
    
    for table in tables:
        items_cursor.execute(f"SELECT price FROM {table} WHERE item = ?", (item_name,))
        result = items_cursor.fetchone()
        if result:
            return result[0]
    
    return None

def get_item_category(items_cursor, item_name):
    """Получает категорию товара из базы данных items.db"""
    tables = ['common', 'unusual', 'rare', 'legendary', 'mythical']
    
    for table in tables:
        items_cursor.execute(f"SELECT 1 FROM {table} WHERE item = ?", (item_name,))
        if items_cursor.fetchone():
            return table
    
    return None

def parse_line(line, items_cursor):
    """Парсит строку формата: timestamp_account_action_item_price"""
    parts = line.strip().split('_')
    
    if len(parts) < 5:
        return None
    
    try:
        # Формат даты: 2025-01-27_18:36_rbuiarkb_Sell_Dough_60
        date_str = parts[0]
        time_str = parts[1]
        account = parts[2]
        action = parts[3]  # Sell или Buy
        
        # Последняя часть - всегда общая цена
        total_price = int(parts[-1])
        
        # Собираем название товара из оставшихся частей
        item_parts = parts[4:-1]
        
        # Преобразуем дату и время в формат для базы данных
        datetime_str = f"{date_str} {time_str}"
        
        # Разбираем товары
        items = []
        
        # Если есть подчеркивания, возможно несколько товаров
        if len(item_parts) > 1:
            # Простая логика для случаев типа Leopard_Leopard
            # Проверяем, все ли части одинаковые
            if len(item_parts) == 2 and item_parts[0] == item_parts[1]:
                # Два одинаковых товара (Leopard_Leopard)
                price_per_item = total_price / 2
                category = get_item_category(items_cursor, item_parts[0])
                
                for i in range(2):
                    items.append({
                        'name': item_parts[0],
                        'price': price_per_item,
                        'category': category
                    })
            else:
                # Разные товары или более сложный случай
                # Пробуем найти товары в базе
                found_items = []
                
                # Сначала пробуем найти целые комбинации
                for i in range(len(item_parts)):
                    for j in range(i + 1, len(item_parts) + 1):
                        candidate = '_'.join(item_parts[i:j])
                        price = get_item_price(items_cursor, candidate)
                        if price is not None:
                            found_items.append({
                                'name': candidate,
                                'price': price,
                                'category': get_item_category(items_cursor, candidate),
                                'start': i,
                                'end': j
                            })
                
                if found_items:
                    # Сортируем по длине (предпочитаем более длинные совпадения)
                    found_items.sort(key=lambda x: x['end'] - x['start'], reverse=True)
                    
                    used_indices = set()
                    final_items = []
                    
                    for item in found_items:
                        # Проверяем, не пересекается ли с уже использованными
                        indices = set(range(item['start'], item['end']))
                        if not indices.intersection(used_indices):
                            final_items.append(item)
                            used_indices.update(indices)
                    
                    # Проверяем, все ли части покрыты
                    if len(used_indices) == len(item_parts):
                        # Все части покрыты
                        items = [{'name': item['name'], 
                                 'price': item['price'], 
                                 'category': item['category']} 
                                for item in final_items]
                    else:
                        # Не все части покрыты, делим поровну
                        price_per_item = total_price / len(item_parts)
                        for part in item_parts:
                            items.append({
                                'name': part,
                                'price': price_per_item,
                                'category': get_item_category(items_cursor, part)
                            })
                else:
                    # Не нашли совпадений, делим поровну
                    price_per_item = total_price / len(item_parts)
                    for part in item_parts:
                        items.append({
                            'name': part,
                            'price': price_per_item,
                            'category': get_item_category(items_cursor, part)
                        })
        else:
            # Один товар
            item_name = item_parts[0] if item_parts else "Unknown"
            category = get_item_category(items_cursor, item_name)
            price = get_item_price(items_cursor, item_name)
            
            items.append({
                'name': item_name,
                'price': price if price is not None else total_price,
                'category': category
            })
        
        # Проверяем сумму цен товаров
        items_total = sum(item['price'] for item in items)
        if abs(items_total - total_price) > 0.01:
            # Корректируем цены для точного совпадения
            ratio = total_price / items_total if items_total > 0 else 1
            for item in items:
                item['price'] = round(item['price'] * ratio, 2)
        
        # Убедимся, что сумма точно равна total_price
        items_total = sum(item['price'] for item in items)
        if abs(items_total - total_price) > 0.01 and items:
            # Распределяем разницу на первый товар
            diff = total_price - items_total
            items[0]['price'] = round(items[0]['price'] + diff, 2)
        
        return {
            'datetime': datetime_str,
            'account': account,
            'action': action,
            'items': items,
            'total_price': total_price
        }
    except (ValueError, IndexError) as e:
        print(f"Ошибка при парсинге строки: {line.strip()} - {e}")
        return None

def process_file(file_path, cursor, items_cursor, id_counter):
    """Обрабатывает один файл и добавляет данные в базу данных"""
    print(f"Обработка файла: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    sale_count = 0
    buy_count = 0
    line_count = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        line_count += 1
        
        data = parse_line(line, items_cursor)
        if not data:
            print(f"  Пропущена строка {line_count}: {line.strip()}")
            continue
        
        try:
            # Определяем, продажа это или покупка
            if data['action'].upper() == 'SELL':
                # Для продаж
                # Пробуем вставить с уникальным ID
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        sale_id = generate_unique_id("S")
                        
                        # Вставляем запись о продаже
                        cursor.execute('''
                            INSERT INTO sales (sale_id, created_at, account, total_amount)
                            VALUES (?, ?, ?, ?)
                        ''', (sale_id, data['datetime'], data['account'], data['total_price']))
                        
                        # Добавляем товары в sales_items
                        for item in data['items']:
                            cursor.execute('''
                                INSERT INTO sales_items (sale_id, item_name, category, price)
                                VALUES (?, ?, ?, ?)
                            ''', (sale_id, item['name'], item['category'], item['price']))
                        
                        sale_count += 1
                        break  # Успешно вставлено
                        
                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed" in str(e) and attempt < max_attempts - 1:
                            # ID уже существует, пробуем снова
                            time.sleep(0.001)  # Короткая пауза
                            continue
                        else:
                            raise  # Повторная ошибка или последняя попытка
                
            elif data['action'].upper() == 'BUY':
                # Для покупок
                # Пробуем вставить с уникальным ID
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        buy_id = generate_unique_id("B")
                        
                        # Вставляем запись о покупке
                        cursor.execute('''
                            INSERT INTO buyings (buy_id, created_at, account, total_amount)
                            VALUES (?, ?, ?, ?)
                        ''', (buy_id, data['datetime'], data['account'], data['total_price']))
                        
                        # Добавляем товары в buyings_items
                        for item in data['items']:
                            cursor.execute('''
                                INSERT INTO buyings_items (buy_id, item_name, category, price)
                                VALUES (?, ?, ?, ?)
                            ''', (buy_id, item['name'], item['category'], item['price']))
                        
                        buy_count += 1
                        break  # Успешно вставлено
                        
                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed" in str(e) and attempt < max_attempts - 1:
                            # ID уже существует, пробуем снова
                            time.sleep(0.001)  # Короткая пауза
                            continue
                        else:
                            raise  # Повторная ошибка или последняя попытка
            
        except Exception as e:
            print(f"  Ошибка при обработке строки {line_count}: {line.strip()}")
            print(f"  Детали: {e}")
            continue
    
    print(f"  Добавлено: {sale_count} продаж, {buy_count} покупок")
    return sale_count + buy_count

def create_tables(cursor):
    """Создает необходимые таблицы в базе данных operations.db"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL,
            account TEXT NOT NULL,
            total_amount INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL,
            account TEXT NOT NULL,
            total_amount INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyings_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL,
            FOREIGN KEY (buy_id) REFERENCES buyings(buy_id) ON DELETE CASCADE
        )
    ''')
    
    print("Таблицы созданы/проверены")

def check_existing_ids(cursor):
    """Проверяет существующие ID в базе данных"""
    print("\nПроверка существующих ID...")
    
    cursor.execute("SELECT COUNT(DISTINCT sale_id) FROM sales")
    unique_sales = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT buy_id) FROM buyings")
    unique_buys = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM buyings")
    total_buys = cursor.fetchone()[0]
    
    print(f"  Продажи: {total_sales} записей, {unique_sales} уникальных ID")
    print(f"  Покупки: {total_buys} записей, {unique_buys} уникальных ID")
    
    if unique_sales != total_sales:
        print("  ВНИМАНИЕ: Есть дубликаты sale_id!")
        cursor.execute('''
            SELECT sale_id, COUNT(*) as cnt 
            FROM sales 
            GROUP BY sale_id 
            HAVING cnt > 1
        ''')
        duplicates = cursor.fetchall()
        for dup in duplicates[:5]:  # Показываем первые 5 дубликатов
            print(f"    {dup[0]}: {dup[1]} раз")
    
    if unique_buys != total_buys:
        print("  ВНИМАНИЕ: Есть дубликаты buy_id!")

def main():
    # Подключаемся к обеим базам данных
    operations_conn = sqlite3.connect('Databases/operations.db')
    items_conn = sqlite3.connect('Databases/items.db')
    
    operations_cursor = operations_conn.cursor()
    items_cursor = items_conn.cursor()
    
    # Создаем таблицы если их нет
    create_tables(operations_cursor)
    
    # Проверяем существующие ID
    check_existing_ids(operations_cursor)
    
    # Очищаем старые данные если нужно
    clear_old = input("\nОчистить старые данные? (y/n): ").lower() == 'y'
    if clear_old:
        operations_cursor.execute("DELETE FROM sales_items")
        operations_cursor.execute("DELETE FROM sales")
        operations_cursor.execute("DELETE FROM buyings_items")
        operations_cursor.execute("DELETE FROM buyings")
        operations_conn.commit()
        print("Старые данные очищены")
    
    # Путь к папке с файлами
    data_folder = "money"
    
    if not os.path.exists(data_folder):
        print(f"Папка {data_folder} не существует!")
        operations_conn.close()
        items_conn.close()
        return
    
    # Собираем все файлы, которые нужно обработать
    files_to_process = []
    
    for filename in os.listdir(data_folder):
        if filename.startswith("2025_") and filename.endswith(".txt"):
            file_path = os.path.join(data_folder, filename)
            files_to_process.append(file_path)
    
    # Сортируем файлы по имени (по дате)
    files_to_process.sort()
    
    if not files_to_process:
        print("Не найдены файлы для обработки!")
        operations_conn.close()
        items_conn.close()
        return
    
    total_operations = 0
    id_counter = {}
    
    print(f"\nНачинаем обработку {len(files_to_process)} файлов...")
    
    # Обрабатываем каждый файл
    for file_path in files_to_process:
        try:
            operations = process_file(file_path, operations_cursor, items_cursor, id_counter)
            total_operations += operations
            operations_conn.commit()
            print(f"✓ Файл {os.path.basename(file_path)} обработан успешно")
        except Exception as e:
            print(f"✗ Ошибка при обработке файла {file_path}: {e}")
            operations_conn.rollback()
    
    # Выводим статистику
    print(f"\n{'='*60}")
    print("ОБРАБОТКА ЗАВЕРШЕНА!")
    print(f"{'='*60}")
    print(f"Всего обработано файлов: {len(files_to_process)}")
    print(f"Всего добавлено операций: {total_operations}")
    
    # Получаем статистику по базе данных
    operations_cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = operations_cursor.fetchone()[0]
    
    operations_cursor.execute("SELECT COUNT(*) FROM buyings")
    buyings_count = operations_cursor.fetchone()[0]
    
    operations_cursor.execute("SELECT COUNT(*) FROM sales_items")
    sales_items_count = operations_cursor.fetchone()[0]
    
    operations_cursor.execute("SELECT COUNT(*) FROM buyings_items")
    buyings_items_count = operations_cursor.fetchone()[0]
    
    operations_cursor.execute("SELECT SUM(total_amount) FROM sales")
    total_sales_amount = operations_cursor.fetchone()[0] or 0
    
    operations_cursor.execute("SELECT SUM(total_amount) FROM buyings")
    total_buyings_amount = operations_cursor.fetchone()[0] or 0
    
    print(f"\n📊 Статистика базы данных:")
    print(f"  Всего продаж: {sales_count}")
    print(f"  Всего покупок: {buyings_count}")
    print(f"  Всего товаров в продажах: {sales_items_count}")
    print(f"  Всего товаров в покупках: {buyings_items_count}")
    print(f"  Общая сумма продаж: {total_sales_amount}")
    print(f"  Общая сумма покупок: {total_buyings_amount}")
    
    # Проверяем уникальность ID после импорта
    check_existing_ids(operations_cursor)
    
    # Показываем примеры данных
    print(f"\n📋 Примеры данных (первые 3 записи каждой таблицы):")
    
    print(f"\nТаблица sales:")
    operations_cursor.execute('SELECT * FROM sales ORDER BY id LIMIT 3')
    for row in operations_cursor.fetchall():
        print(f"  {row[0]}_{row[1]}_{row[2]}_{row[3]}_{row[4]}")
    
    print(f"\nТаблица sales_items (товары первой продажи):")
    operations_cursor.execute('''
        SELECT si.id, si.sale_id, si.item_name, si.category, si.price 
        FROM sales_items si 
        WHERE si.sale_id = (SELECT sale_id FROM sales ORDER BY id LIMIT 1)
        ORDER BY si.id
    ''')
    for row in operations_cursor.fetchall():
        print(f"  {row[0]}_{row[1]}_{row[2]}_{row[3]}_{row[4]}")
    
    print(f"\nТаблица buyings:")
    operations_cursor.execute('SELECT * FROM buyings ORDER BY id LIMIT 3')
    for row in operations_cursor.fetchall():
        print(f"  {row[0]}_{row[1]}_{row[2]}_{row[3]}_{row[4]}")
    
    print(f"\nТаблица buyings_items (товары первой покупки):")
    operations_cursor.execute('''
        SELECT bi.id, bi.buy_id, bi.item_name, bi.category, bi.price 
        FROM buyings_items bi 
        WHERE bi.buy_id = (SELECT buy_id FROM buyings ORDER BY id LIMIT 1)
        ORDER BY bi.id
    ''')
    for row in operations_cursor.fetchall():
        print(f"  {row[0]}_{row[1]}_{row[2]}_{row[3]}_{row[4]}")
    
    # Закрываем соединения
    operations_conn.close()
    items_conn.close()
    
    print(f"\n✅ Все операции завершены успешно!")

if __name__ == "__main__":
    main()