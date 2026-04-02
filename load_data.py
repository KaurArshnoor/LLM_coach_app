#!/usr/bin/env python3
"""Minimal data loader for exercises CSV"""
import csv
import psycopg2
from psycopg2.extras import execute_values
from config import DB_URL

def load_data(csv_file, db_config):
    """Load CSV into database with validation."""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Read CSV
    with open(csv_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            {k: (v.strip() if isinstance(v, str) and v.strip() else None)
             for k, v in row.items() if k and k.strip()}
            for row in reader
        ]

    # Insert
    columns = [c for c in rows[0].keys() if c and c.strip()]
    cols_sql = ', '.join(columns)
    query = f"INSERT INTO exercises ({cols_sql}) VALUES %s"
    values = [[row.get(col) for col in columns] for row in rows]

    execute_values(cursor, query, values)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM exercises")
    count = cursor.fetchone()[0]
    print(f"Loaded {count} exercises")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    import sys
    config = {
        'host': 'localhost',
        'database': 'coaching_app_db',
        'user': 'postgres',
        'password': 'postgres',
    }
    load_data(sys.argv[1] if len(sys.argv) > 1 else 'exercises.csv', config)
