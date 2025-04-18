from src.db import init_db
from src.telegram_handler import start_telegram_bot, init_bots
from src.pb_config import init_pb_config

def main():
    init_db()
    init_bots()
    init_pb_config()
    start_telegram_bot()

if __name__ == '__main__':
    main()
