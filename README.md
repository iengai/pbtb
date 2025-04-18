# pbtb
a telegram bot to control the passivbot

## run bot
``
python mian.py
``

## Register and start the service on boot
```
chmod +x bin/install_pbtb_service.sh
./bin/install_pbtb_service.sh
```

## config
`bot_token`:  Telegram bot token
`allowed_user_ids`： Telegram user IDs allowed to control the bot
`passivbot_env_python`: Path to the Python used for Passivbot execution. Can be a virtual environment
`passivbot_dir`: Absolute path to the Passivbot directory
`predefined_configs_dir`: Directory containing predefined Passivbot configurations
`user_configs_dir`: Directory containing user-specific configurations