import os
import sys
import sqlite3

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'app.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table info
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user';")
print("User table schema:")
print(cursor.fetchone()[0])

conn.close() 