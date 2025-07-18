#!/usr/bin/env bash
# File for setting up logger version os owlogger
# must be run as root (e.g. sudo)

# Check if the script is run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ This script must be run as root. Try using sudo."
  exit 1
fi

# Logger program
mkdir -p              /usr/local/lib/owlogger
cp owlogger.py        /usr/local/lib/owlogger
cp air-datepicker.js  /usr/local/lib/owlogger
cp air-datepicker.css /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
cp owlogger.toml      /etc/owlogger

# database location
mkdir -p  /var/lib/owlogger
chown -R www-data:www-data /var/lib/owlogger
chmod 770 /var/lib/owlogger

# systemd file
cp owlogger.service /etc/systemd/system
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable owlogger.service
systemctl start  owlogger.service
systemctl status owlogger.service

