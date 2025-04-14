import os
import json
import shutil

with open("config.json") as f:
    CONFIG_FILE = json.load(f)

PB_DIR_PATH = CONFIG_FILE['passivbot_dir']
VENV_PYTHON = CONFIG_FILE['env_python']
USER_CONFIGS_DIR = CONFIG_FILE['user_configs_dir']
PREDEFINED_DIR = CONFIG_FILE['predefined_configs_dir']
SILENT_CONFIG = os.path.join(PREDEFINED_DIR, 'silent.json')

API_KEYS_FILE = os.path.join(PB_DIR_PATH, 'api-keys.json')

MAIN_SCRIPT = 'main.py'
DB_PATH = 'sqlite'

BOT_TOKEN = CONFIG_FILE['bot_token']
ALLOWED_USER_IDS = CONFIG_FILE.get('allowed_user_ids', [CONFIG_FILE['allowed_user_ids']])

def get_api_key_file():
    if not os.path.exists(API_KEYS_FILE):
        shutil.copy(API_KEYS_FILE + '.example', API_KEYS_FILE)
    return API_KEYS_FILE
