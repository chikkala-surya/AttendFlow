import sqlite3

conn = sqlite3.connect('attendance.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute('''
INSERT OR IGNORE INTO admins(username,password)
VALUES('surya','admin123')
''')

conn.commit()
conn.close()

print("Database created")