"""檢查資料庫中的表"""
import sqlite3

conn = sqlite3.connect('nm_stewardship.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("資料庫中的表：")
for table in tables:
    print(f"  - {table[0]}")
conn.close()

