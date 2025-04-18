#!/bin/bash

SERVICE_NAME="pbtb.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo "Creating $SERVICE_NAME..."

# warning: use correct python env
cat <<EOF | sudo tee $SERVICE_PATH > /dev/null
[Unit]
Description=Run pbtb Python bot on startup
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/nohup /home/ec2-user/passivbot/venv/bin/python /home/ec2-user/pbtb/main.py
WorkingDirectory=/home/ec2-user/pbtb
StandardOutput=append:/home/ec2-user/pbtb/logs.log
StandardError=append:/home/ec2-user/pbtb/logs.log
Restart=always
User=ec2-user
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# set permission
sudo chmod 644 $SERVICE_PATH

# register
echo "Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# check status
sudo systemctl status $SERVICE_NAME
