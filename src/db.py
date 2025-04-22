import sqlite3
from .config import DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                bot_id TEXT PRIMARY KEY,
                user_id TEXT not null,
                enabled BOOLEAN DEFAULT FALSE,
                apikey TEXT NOT NULL,
                secret TEXT NOT NULL
            );
        ''')

def bot_exists(bot_id):
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute('SELECT 1 FROM bots WHERE bot_id = ?', (bot_id,)).fetchone()
        return result is not None

def list_all_bots(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute('SELECT bot_id FROM bots WHERE user_id=?', (user_id,)).fetchall()

def list_all_enabled_bots():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute('SELECT bot_id FROM bots WHERE enabled=1').fetchall()

def add_bot(bot_id, user_id, apikey, secret):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO bots (bot_id, user_id, enabled, apikey, secret)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(bot_id) DO UPDATE SET
                apikey = excluded.apikey,
                secret = excluded.secret
        ''', (bot_id, user_id, apikey, secret))

def set_enabled(bot_id, enabled):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE bots SET enabled=? WHERE bot_id=?', (enabled, bot_id))