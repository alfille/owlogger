#!/usr/bin/env bash
# File for setting up internal transmitter component of owlogger
# must be run as root (e.g. sudo)

# Check if the script is run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ This script must be run as root. Try using sudo."
  exit 1
fi

# Debian/Ubuntu Specific
# apt update
# apt upgrade
# apt install python3 python3-jwt python3-bcrypt git owserver

# Logger program
mkdir -p              /usr/local/lib/owlogger
cp owpost.py        /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
cp owpost.toml      /etc/owlogger
chown -R www-data:www-data /etc/owlogger/owpost.toml
chmod 660             /etc/owlogger/owpost.toml

# script to run owlog_user
cp owpost /usr/bin
chmod +x /usr/bin/owpost

# systemd file
cp owpost.service /etc/systemd/system
cp owpost.timer   /etc/systemd/system
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable owpost.service
systemctl start  owpost.service
systemctl status owpost.service

