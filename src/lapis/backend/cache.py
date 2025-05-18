'''
SQLite DB used to store user seeds as a cache
Reduces # of GET requests if user calls a lot of seedInfoFns - all of which use a seed
'''


import sqlite3
import os

conn = sqlite3.connect(os.getenv("SEED_CACHE"))
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_seeds (
    user_id TEXT PRIMARY KEY,
    seed TEXT
)""")
conn.commit()

def cache_user_seed(user_id, seed):
    current = get_cached_seed(user_id)
    if current != seed:
        cursor.execute("""
            REPLACE INTO user_seeds (user_id, seed)
            VALUES (?, ?)
        """, (str(user_id), seed))
        conn.commit()

def get_cached_seed(user_id):
    cursor.execute("SELECT seed FROM user_seeds WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    return row[0] if row else None

def invalidate_user_cache(user_id):
    cursor.execute("DELETE FROM user_seeds WHERE user_id = ?", (str(user_id),))
    conn.commit()
