import json
import os
import shutil
import subprocess
import signal
from .db import add_bot as db_add_bot
from .config import USER_CONFIGS_DIR, MAIN_SCRIPT, VENV_PYTHON, SILENT_CONFIG, get_api_key_file

def build_start_cmd(bot_id):
    config_path = os.path.join(USER_CONFIGS_DIR, f"{bot_id}.json")
    log_file = f"{bot_id}.log"
    return f"nohup {VENV_PYTHON} {MAIN_SCRIPT} {config_path} > {log_file} 2>&1 &"

def get_bot_pid_if_running(bot_id):
    config_path = os.path.join(USER_CONFIGS_DIR, f"{bot_id}.json")
    search_str = f"{VENV_PYTHON} {MAIN_SCRIPT} {config_path}"
    try:
        output = subprocess.check_output(["ps", "aux"], text=True)
        for line in output.splitlines():
            if search_str in line and 'grep' not in line:
                return int(line.split()[1])
        return None
    except Exception:
        return None

def start_bot(bot_id):
    os.system(build_start_cmd(bot_id))

def stop_bot(bot_id):
    pid = get_bot_pid_if_running(bot_id)
    if pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

def add_bot(bot_id, user_id, apikey, secret):
    apikey_file = get_api_key_file()
    with open(apikey_file, 'r') as f:
        api_data = json.load(f)

    api_data[bot_id] = {
        "exchange": "bybit",
        "key": apikey,
        "secret": secret
    }
    with open(apikey_file, 'w') as f:
        json.dump(api_data, f, indent=4)

    bot_config = USER_CONFIGS_DIR + f"{bot_id}.json"
    if not os.path.exists(bot_config):
        shutil.copy(SILENT_CONFIG, bot_config)
    db_add_bot(bot_id, user_id, bot_config, apikey, secret)