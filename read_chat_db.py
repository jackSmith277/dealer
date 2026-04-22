import sqlite3
import os

db_path = r'd:\dealer\dealer\chat_backup.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for table in tables:
    print(f"\n=== Table: {table[0]} ===")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print("Columns:", [c[1] for c in columns])
    
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")

conn.close()
