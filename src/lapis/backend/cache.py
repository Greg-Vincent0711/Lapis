'''
SQLite DB used to store user seeds as a cache/
Reduces # of GET requests to DynamoDB if user calls a lot of seedInfoFns - all of which use a seed


Some notes about this now that I'm hosting the bot on microservice architecture
Because this cache uses a SQLite File, it can't be easily persisted(consistent) across
stateful portions of Lapis(lapis.py for ex) and stateless portions like db.py and 
seed_impl.py. If the cache is updated from the setSeed fn, that only updates what lives on
the stateful portion(lapis.py on ec2). Since I don't anticipate much traffic it isn't worth it
to use the cache in my opinion. Not unless this project really grows.

cache.py will still be used for tests, since those take place only on Github Actions
'''
import sqlite3
import os


def get_connection_and_cursor():
    conn = sqlite3.connect(os.getenv("SEED_CACHE"))
    cursor = conn.cursor()
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {os.getenv("CACHE_TABLE")} (
        user_id TEXT PRIMARY KEY,
        seed TEXT
    )""")
    conn.commit()
    return conn, cursor


def cache_user_seed(user_id, seed):
    conn, cursor = get_connection_and_cursor()
    current = get_cached_seed(user_id)
    if current != seed:
        cursor.execute(f"""
            REPLACE INTO {os.getenv('CACHE_TABLE')} (user_id, seed)
            VALUES (?, ?)
        """, (str(user_id), seed))
        conn.commit()

def get_cached_seed(user_id):
    _, cursor = get_connection_and_cursor()
    cursor.execute(f"SELECT seed FROM {os.getenv('CACHE_TABLE')} WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    return row[0] if row else None

# may not be used until project becomes more complex
def invalidate_user_cache(user_id):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f"DELETE FROM {os.getenv('CACHE_TABLE')} WHERE user_id = ?", (str(user_id),))
    conn.commit()
