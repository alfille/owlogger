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
cp owlog_user.py      /usr/local/lib/owlogger
cp air-datepicker.js  /usr/local/lib/owlogger
cp air-datepicker.css /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
cp owlogger.toml      /etc/owlogger

# database location
#  create an empty database file to ensure permissions and ownership are correct
mkdir -p  /var/lib/owlogger
touch /var/lib/owlogger/logger_data.db
chown -R www-data:www-data /var/lib/owlogger
chmod 770 /var/lib/owlogger
chmod 660 /var/lib/owlogger/logger_data.db

# script to run owlog_user
cp owlog_user /usr/bin
chmod +x /usr/bin/owlog_user

# systemd file
cp owlogger.service /etc/systemd/system
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable owlogger.service
systemctl start  owlogger.service
systemctl status owlogger.service

