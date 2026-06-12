import sqlite3

conn = sqlite3.connect('attendance.db')

cursor = conn.cursor()

cursor.execute("""
ALTER TABLE employees
ADD COLUMN admin_id INTEGER
""")

conn.commit()

conn.close()

print("Database Updated Successfully")
