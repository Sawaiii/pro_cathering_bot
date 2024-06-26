import sqlite3

def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER NOT NULL,
        username TEXT,
        CONSTRAINT unique_telegram_id UNIQUE (telegram_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        order_date TEXT,
        portions INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menus (
        id INTEGER PRIMARY KEY,
        menu_date TEXT UNIQUE,
        menu_text TEXT
    )
    ''')

    conn.commit()
    conn.close()

def save_user(telegram_id, username):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user_id = cursor.fetchone()[0]

    conn.close()
    return user_id

def get_menu_by_id(menu_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menus WHERE id = ?", (menu_id,))
    menu = cursor.fetchone()
    conn.close()
    return menu

def delete_menu(menu_date):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menus WHERE menu_date = ?", (menu_date,))
    cursor.execute("DELETE FROM orders WHERE order_date = ?", (menu_date,))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def save_order(user_id, order_date, portions):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM orders WHERE user_id = ? AND order_date = ?", (user_id, order_date))
    existing_order = cursor.fetchone()

    if existing_order:
        cursor.execute("UPDATE orders SET portions = ? WHERE id = ?", (portions, existing_order[0]))
    else:
        cursor.execute("INSERT INTO orders (user_id, order_date, portions) VALUES (?, ?, ?)", (user_id, order_date, portions))

    conn.commit()
    conn.close()

def get_user_orders(user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def save_menu(menu_date, menu_text):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO menus (menu_date, menu_text) VALUES (?, ?)", (menu_date, menu_text))
    conn.commit()
    conn.close()

def get_menu_by_date(menu_date):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menus WHERE menu_date = ?", (menu_date,))
    menu = cursor.fetchone()
    conn.close()
    return menu

def get_all_menus():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menus")
    menus = cursor.fetchall()
    conn.close()
    return menus

def get_all_orders():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT orders.id, users.telegram_id, users.username, orders.order_date, orders.portions FROM orders INNER JOIN users ON orders.user_id = users.id")
    orders = cursor.fetchall()
    conn.close()
    return orders