from src.db import init_db
from src.telegram_handler import start_telegram_bot, init_bots

def main():
    init_db()
    init_bots()
    start_telegram_bot()

if __name__ == '__main__':
    main()
