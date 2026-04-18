import sqlite3


with sqlite3.connect('Databases/operations.db') as conn:
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account TEXT NOT NULL,
            total_amount INT NOT NULL)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account TEXT NOT NULL,
            total_amount INT NOT NULL)
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyings_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL,
            FOREIGN KEY (buy_id) REFERENCES sales(buy_id) ON DELETE CASCADE
        )
        ''')
    
    conn.commit()


with sqlite3.connect('Databases/accounts.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container1 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container1 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container2 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container2 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container3 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container3 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container4 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container4 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container5 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container5 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container6 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container6 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container7 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container7 (item, quantity) VALUES (?,?)', products)
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Container8 (
        item TEXT,
        quantity INT)
    ''')
    products = [
        ('item1', 0),
        ('item2', 2),
        ('item3', 0),
        ('item4', 0),
        ('item5', 5),
        ('item6', 6),
        ('item7', 0),
        ('item8', 5),
        ('item9', 4),
        ('item10', 0),
        ('item11', 2),
        ('item12', 3),
        ('item13', 2),
        ('item14', 2),
        ('item15', 5),
        ('item16', 2),
        ('item17', 5),
        ('item18', 11),
        ('item19', 4),
        ('item20', 4),
        ('item21', 14),
        ('item22', 10),
        ('item23', 3),
        ('item24', 8),
        ('item25', 0),
        ('item26', -1),
        ('item27', -2),
        ('item28', 5),
        ('item29', 4),
        ('item30', 2),
        ('item31', 2),
        ('item32', 1),
        ('item33', 1),
        ('item34', 1),
        ('item35', 1),
        ('item36', 2),
        ('item37', 1),
        ('item38', 225),
        ('item38', 0),
        ('item39', 1),
        ('item40', 0),
        ('item41', 0)
    ]
    cursor.executemany('INSERT INTO Container8 (item, quantity) VALUES (?,?)', products)
    conn.commit()
with sqlite3.connect('Databases/items.db') as conn:
   cursor = conn.cursor()
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS category1 (
       item TEXT,
       price INT)
   ''')
   products = [
       ('item1',0),
       ('item2',0),
       ('item3',0),
       ('item4',0),
       ('item5',0),
       ('item6',0),
       ('item7',0)
   ]
   cursor.executemany('INSERT INTO category1 (item,price) VALUES (?,?)', products)
   conn.commit()
   cursor.execute('''
   SELECT * FROM category1
   ''')
   rows = cursor.fetchall()
   print("Таблица 'category1':")
   print("-" * 30)
   for row in rows:
       print(f"Товар: {row[0]}, Цена: {row[1]}")
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS category2 (
       item TEXT,
       price INT)
   ''')
   products = [
       ('item1',0),
       ('item2',0),
       ('item3',0),
       ('item4',0),
       ('item5',0),
       ('item6',0)
   ]
   cursor.executemany('INSERT INTO category2 (item,price) VALUES (?,?)', products)
   conn.commit()
   cursor.execute('''
   SELECT * FROM category2
   ''')
   rows = cursor.fetchall()
   print("Таблица 'category2':")
   print("-" * 30)
   for row in rows:
       print(f"Товар: {row[0]}, Цена: {row[1]}")
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS category3 (
       item TEXT,
       price INT)
   ''')
   products = [
       ('item1',0),
       ('item2',0),
       ('item3',0),
       ('item4',0),
       ('item5',0)
   ]
   cursor.executemany('INSERT INTO category3 (item,price) VALUES (?,?)', products)
   conn.commit()
   cursor.execute('''
   SELECT * FROM category3
   ''')
   rows = cursor.fetchall()
   print("Таблица 'category3':")
   print("-" * 30)
   for row in rows:
       print(f"Товар: {row[0]}, Цена: {row[1]}")
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS category4 (
       item TEXT,
       price INT)
   ''')
   products = [
       ('item1',10),
       ('item2',30),
       ('item3',10),
       ('item4',30),
       ('item5',10),
       ('item6',10),
       ('item7',10),
       ('item8',30),
       ('item9',50),
       ('item10',50),
       ('item11',20)
   ]
   cursor.executemany('INSERT INTO category4 (item,price) VALUES (?,?)', products)
   conn.commit()
   cursor.execute('''
   SELECT * FROM category4
   ''')
   rows = cursor.fetchall()
   print("Таблица 'category4':")
   print("-" * 30)
   for row in rows:
       print(f"Товар: {row[0]}, Цена: {row[1]}")
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS category5 (
       item TEXT,
       price INT)
   ''')
   products = [
       ('item1',50),
       ('item2',30),
       ('item3',40),
       ('item4',60),
       ('item5',20),
       ('item6',30),
       ('item7',80),
       ('item8',30),
       ('item9',70),
       ('item10',150),
       ('item11',300),
       ('item12',50),
       ('item13',1000)
   ]
   cursor.executemany('INSERT INTO category5 (item,price) VALUES (?,?)', products)
   conn.commit()
   cursor.execute('''
   SELECT * FROM category5
   ''')
   rows = cursor.fetchall()
   print("Таблица 'category5':")
   print("-" * 30)
   for row in rows:
       print(f"Товар: {row[0]}, Цена: {row[1]}")


