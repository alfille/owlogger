#!/bin/sh
# File for setting up internal transmitter component of owlogger
# must be run as root (e.g. sudo)

echo
echo "-------------------------------"
echo "OWPOST install process starting"

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

# Debian/Ubuntu Specific
# apt update
# apt upgrade
# apt install python3 python3-jwt python3-bcrypt git owserver

# Logger program
mkdir -p          /usr/local/lib/owlogger
\cp owpost.py     /usr/local/lib/owlogger
\cp owposttext.py /usr/local/lib/owlogger
\cp -R pyownet    /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
cp -i owpost.toml     /etc/owlogger
chown -R $USER:$GROUP /etc/owlogger/owpost.toml
chmod 660             /etc/owlogger/owpost.toml

# script to run owlog_user
\cp owpost     /usr/bin
\cp owposttext /usr/bin
chmod +x       /usr/bin/owpost
chmod +x       /usr/bin/owposttext

# systemd file
cp -i owpost.service /etc/systemd/system
cp -i owpost.timer   /etc/systemd/system
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable owpost.service
systemctl start  owpost.service
systemctl enable owpost.timer
systemctl start  owpost.timer
systemctl status --no-pager owpost.service
systemctl status --no-pager owpost.timer

echo "OWPOST install process finished"
echo "-------------------------------"
echo
