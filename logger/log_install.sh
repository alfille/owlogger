#!/bin/sh
# Script for setting up external server component of owlogger
# must be run as root (e.g. sudo)

# Debian/Ubuntu Specific
# apt update
# apt upgrade
# apt install python3 python3-jwt python3-bcrypt git ufw caddy

echo
echo "---------------------------------"
echo "OWLOGGER install process starting"

# Check if the effective user ID is 0 using the 'id -u' command
if [ "$(id -u)" -ne 0 ]; then
  echo "Error: This script must be run as root or with sudo." >&2
  # Try to suggest how to run it if sudo is available and the user isn't already root
  if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then
    echo "Please run: sudo \"$0\" \"$@\"" >&2
  fi
  exit 1
fi

# Create user/group
# Define the user and group names
GROUP="www-data"
 USER="www-data"

# --- Group Creation ---
if getent group "$GROUP" >/dev/null; then
  echo $GROUP
else
  groupadd "$GROUP"
  if [ $? -ne 0 ]; then
    echo "Error creating group '$GROUP'. Aborting." >&2
    exit 1
  fi
fi

# --- User Creation ---
if getent passwd "$USER" >/dev/null; then
  echo $USER
else
  echo "User '$NEW_USER' does not exist. Creating it..."
  sudo useradd -r -g "$GROUP"  "$USER"
  if [ $? -ne 0 ]; then
    echo "Error creating user '$USER'. Aborting." >&2
    exit 1
  fi
fi

# Logger program
mkdir -p               /usr/local/lib/owlogger
\cp owlogger.py        /usr/local/lib/owlogger
\cp owlog_user.py      /usr/local/lib/owlogger
\cp air-datepicker.js  /usr/local/lib/owlogger
\cp air-datepicker.css /usr/local/lib/owlogger
\cp favicon.ico        /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
cp -i owlogger.toml   /etc/owlogger
chown -R $USER:$GROUP /etc/owlogger/owlogger.toml
chmod 660             /etc/owlogger/owlogger.toml

# database location
#  create an empty database file to ensure permissions and ownership are correct
mkdir -p              /var/lib/owlogger
touch                 /var/lib/owlogger/logger_data.db
chown -R $USER:$GROUP /var/lib/owlogger
chmod 770             /var/lib/owlogger
chmod 660             /var/lib/owlogger/logger_data.db

# script to run owlog_user
\cp owlog_user /usr/bin
chmod +x       /usr/bin/owlog_user

# systemd file
cp -i owlogger.service /etc/systemd/system
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable owlogger.service
systemctl start  owlogger.service
systemctl status owlogger.service

echo "OWLOGGER install process finished"
echo "---------------------------------"
echo
