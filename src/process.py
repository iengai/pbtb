import json
import os
import shutil
import subprocess
import signal
from .db import add_bot as db_add_bot
from .config import PB_MAIN_SCRIPT, PB_VENV_PYTHON, SILENT_CONFIG, get_api_key_file, PB_DIR_PATH
from .pb_config import get_pb_config

def build_start_cmd(bot_id):
    config_path = get_pb_config(bot_id)
    log_file = os.path.join(PB_DIR_PATH, f"logs/{bot_id}.log")
    return f"nohup {PB_VENV_PYTHON} {PB_MAIN_SCRIPT} {config_path} > {log_file} 2>&1 &"

def get_bot_pid_if_running(bot_id):
    config_path = get_pb_config(bot_id)
    search_str = f"{PB_VENV_PYTHON} {PB_MAIN_SCRIPT} {config_path}"
    try:
        output = subprocess.check_output(["ps", "aux"], text=True)
        for line in output.splitlines():
            if search_str in line and 'grep' not in line:
                return int(line.split()[1])
        return None
    except Exception:
        return None

def start_bot(bot_id):
    pid = get_bot_pid_if_running(bot_id)
    if pid is not None:
        return
    subprocess.run(build_start_cmd(bot_id), shell=True, check=True, preexec_fn=os.setsid,cwd=PB_DIR_PATH)

def stop_bot(bot_id):
    pid = get_bot_pid_if_running(bot_id)
    if pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

def restart_bot(bot_id):
    stop_bot(bot_id)
    start_bot(bot_id)

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

    bot_config = get_pb_config(bot_id)
    if not os.path.exists(bot_config):
        shutil.copy(SILENT_CONFIG, bot_config)
    db_add_bot(bot_id, user_id, apikey, secret)