import os
import json
from .config import USER_CONFIGS_DIR, PREDEFINED_DIR

def init_pb_config():
    if not os.path.exists(PREDEFINED_DIR):
        os.makedirs(PREDEFINED_DIR)
    if not os.path.exists(USER_CONFIGS_DIR):
        os.makedirs(USER_CONFIGS_DIR)

def apply_pb_config(bot_id, pb_config):
    pb_config_path = os.path.join(PREDEFINED_DIR, pb_config)
    if not os.path.isfile(pb_config_path):
        raise FileNotFoundError(f"Config file '{pb_config}' does not exist in {PREDEFINED_DIR}")

    with open(pb_config_path) as f:
        template = json.load(f)

    keys_to_copy = [
        ('bot', 'long'),
        ('bot', 'short'),
        ('live', 'approved_coins'),
        ('live', 'coin_flags'),
    ]

    bot_config_path = get_pb_config(bot_id)
    with open(bot_config_path) as f:
        bot_config = json.load(f)

    for path in keys_to_copy:
        src = template
        dst = bot_config
        for key in path[:-1]:
            src = src.get(key, {})
            dst = dst.get(key, {})
        dst[path[-1]] = src.get(path[-1], dst.get(path[-1]))

    bot_config["name"] = template["name"]
    bot_config['live']['user'] = bot_id

    with open(bot_config_path, 'w') as f:
        json.dump(bot_config, f, indent=4)

def list_predefined():
    return [f for f in os.listdir(PREDEFINED_DIR) if f.endswith('.json')]

def get_pb_config(bot_id):
    return os.path.join(USER_CONFIGS_DIR, f"{bot_id}.json")