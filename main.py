import argparse
from src.db import init_db, bot_exists, set_selected_bot, list_all_bots
from src.process import start_bot, stop_bot, get_bot_pid_if_running
from src.pb_config import apply_pb_config, list_predefined
from src.telegram_handler import start_telegram_bot

def cli_list(user_id):
    bots = list_all_bots(user_id)
    output = []
    for bot_id, is_selected in bots:
        pid = get_bot_pid_if_running(bot_id)
        status = "Running" if pid else "Stopped"
        tag = "[SELECTED]" if is_selected else ""
        output.append(f"{bot_id} - {status} {tag}")
    print("\n".join(output) if output else "No bots available.")

def cli_start(bot_id):
    if not bot_exists(bot_id):
        print(f"[ERROR] Bot '{bot_id}' does not exist.")
        return
    start_bot(bot_id)
    print(f"✅ Started bot: {bot_id}")

def cli_stop(bot_id):
    if not bot_exists(bot_id):
        print(f"[ERROR] Bot '{bot_id}' does not exist.")
        return
    stop_bot(bot_id)
    print(f"🛑 Stopped bot: {bot_id}")

def cli_select(bot_id):
    if not bot_exists(bot_id):
        print(f"[ERROR] Bot '{bot_id}' does not exist.")
        return
    set_selected_bot(bot_id)
    print(f"📌 Selected bot: {bot_id}")

def cli_configure(bot_id):
    if not bot_exists(bot_id):
        print(f"[ERROR] Bot '{bot_id}' does not exist.")
        return

    templates = list_predefined()
    if not templates:
        print("No templates found.")
        return

    print("Available templates:")
    for idx, path in enumerate(templates):
        print(f"[{idx}] {path}")

    try:
        choice = int(input("Select template index: "))
        apply_pb_config(bot_id, choice)
        print(f"✅ Applied template and restarted bot: {bot_id}")
    except (IndexError, ValueError):
        print("❌ Invalid template index.")
    except Exception as e:
        print(f"❌ Error during configuration: {e}")

def main():
    init_db()

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['cli', 'telegram'], default='cli')
    parser.add_argument('command', nargs='?', help='Command: list/start/stop/select/configure (cli only)')
    parser.add_argument('--bot', help='Bot ID to operate on')
    parser.add_argument('--user', help='User ID to operate on')
    args = parser.parse_args()

    if args.mode == 'telegram':
        start_telegram_bot()
        return

    # CLI mode logic
    if args.command == 'list':
        cli_list(args.user)
    elif args.command == 'start':
        if args.bot:
            cli_start(args.bot)
        else:
            print("❗ Missing --bot argument.")
    elif args.command == 'stop':
        if args.bot:
            cli_stop(args.bot)
        else:
            print("❗ Missing --bot argument.")
    elif args.command == 'select':
        if args.bot:
            cli_select(args.bot)
        else:
            print("❗ Missing --bot argument.")
    elif args.command == 'configure':
        if args.bot:
            cli_configure(args.bot)
        else:
            print("❗ Missing --bot argument.")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
