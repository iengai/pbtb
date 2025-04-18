import json
import os
import subprocess
import signal
from .db import add_bot as db_add_bot
from .config import PB_MAIN_SCRIPT, PB_VENV_PYTHON, get_api_key_file, PB_DIR_PATH
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
        with open(bot_config, 'w') as f:
            silent_config = get_silent_config_content()
            silent_config["live"]["user"] = bot_id
            json.dump(silent_config, f, indent=4)
    db_add_bot(bot_id, user_id, apikey, secret)

def get_silent_config_content():
    return {
        "bot": {
            "long": {"close_grid_markup_range": 0.0076185,
                  "close_grid_min_markup": 0.002665,
                  "close_grid_qty_pct": 0.96044,
                  "close_trailing_grid_ratio": -0.0088751,
                  "close_trailing_qty_pct": 0.75703,
                  "close_trailing_retracement_pct": 0.094468,
                  "close_trailing_threshold_pct": 0.033725,
                  "ema_span_0": 321.67,
                  "ema_span_1": 320.53,
                  "enforce_exposure_limit": True,
                  "entry_grid_double_down_factor": 1.6886,
                  "entry_grid_spacing_pct": 0.027326,
                  "entry_grid_spacing_weight": 1.1331,
                  "entry_initial_ema_dist": -0.099207,
                  "entry_initial_qty_pct": 0.010642,
                  "entry_trailing_grid_ratio": -0.016706,
                  "entry_trailing_retracement_pct": 0.02615,
                  "entry_trailing_threshold_pct": 0.055202,
                  "filter_relative_volume_clip_pct": 0.0053335,
                  "filter_rolling_window": 309.75,
                  "n_positions": 0,
                  "total_wallet_exposure_limit": 0.87819,
                  "unstuck_close_pct": 0.036772,
                  "unstuck_ema_dist": -0.078578,
                  "unstuck_loss_allowance_pct": 0.030858,
                  "unstuck_threshold": 0.56304},
         "short": {"close_grid_markup_range": 0.022568,
                   "close_grid_min_markup": 0.0082649,
                   "close_grid_qty_pct": 0.53985,
                   "close_trailing_grid_ratio": 0.52698,
                   "close_trailing_qty_pct": 0.71696,
                   "close_trailing_retracement_pct": 0.01282,
                   "close_trailing_threshold_pct": -0.005394,
                   "ema_span_0": 1212.7,
                   "ema_span_1": 659.66,
                   "enforce_exposure_limit": True,
                   "entry_grid_double_down_factor": 0.72508,
                   "entry_grid_spacing_pct": 0.017338,
                   "entry_grid_spacing_weight": 4.0792,
                   "entry_initial_ema_dist": 0.0026837,
                   "entry_initial_qty_pct": 0.014787,
                   "entry_trailing_grid_ratio": 0.18122,
                   "entry_trailing_retracement_pct": 0.018165,
                   "entry_trailing_threshold_pct": 0.062005,
                   "filter_relative_volume_clip_pct": 0.57973,
                   "filter_rolling_window": 320.18,
                   "n_positions": 0,
                   "total_wallet_exposure_limit": 0.0,
                   "unstuck_close_pct": 0.088717,
                   "unstuck_ema_dist": -0.014418,
                   "unstuck_loss_allowance_pct": 0.030868,
                   "unstuck_threshold": 0.68942}},
        "live": {"approved_coins": {"long": {},"short": {}},
          "auto_gs": True,
          "coin_flags": {},
          "empty_means_all_approved": True,
          "execution_delay_seconds": 2.0,
          "filter_by_min_effective_cost": True,
          "forced_mode_long": "",
          "forced_mode_short": "",
          "ignored_coins": {"long": [], "short": []},
          "leverage": 5.0,
          "market_orders_allowed": True,
          "max_n_cancellations_per_batch": 5,
          "max_n_creations_per_batch": 3,
          "max_n_restarts_per_day": 10,
          "minimum_coin_age_days": 30.0,
          "ohlcvs_1m_rolling_window_days": 4.0,
          "ohlcvs_1m_update_after_minutes": 10.0,
          "pnls_max_lookback_days": 30.0,
          "price_distance_threshold": 0.002,
          "time_in_force": "good_till_cancelled",
          "user": "bybit_01"},
 }
