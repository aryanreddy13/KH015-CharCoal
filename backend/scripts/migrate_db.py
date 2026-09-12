import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "disaster.db")
if not os.path.exists(db_path):
    print("Database file not found at", db_path)
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(reports);")
existing_cols = [row[1] for row in cursor.fetchall()]
print("Existing reports columns:", existing_cols)

cols_to_add = [
    ("reporter_name", "TEXT DEFAULT 'Citizen Reporter'"),
    ("reporter_phone", "TEXT"),
    ("location_text", "TEXT"),
    ("admin_notes", "TEXT"),
]

for col_name, col_def in cols_to_add:
    if col_name not in existing_cols:
        print(f"Adding column {col_name} to reports table...")
        cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_def};")

conn.commit()
conn.close()
print("Database schema migration verified successfully!")
