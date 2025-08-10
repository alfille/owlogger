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

name="owpost"
messages=""

# Help message function
show_help() {
  echo "Usage: $0 [-n name] [-h]"
  echo
  echo "Options:"
  echo "  -n NAME     Set owpost name (for multiple instances) (default: $name)"
  echo "  -m          messages only, no owserver needed"
  echo "  -h          Show this help message"
  echo
}

while getopts "n:mh" opt ; do
    case $opt in
     n) name=$OPTARG ;;
     m) messages="#" ;;
     h) show_help; exit 0 ;;
     \?) echo "Unrecognized argument: -$OPTARGS" >&2; show help ; exit 1 ;;
    esac
done

echo "---- Installing as $name -----"
toml="$name.toml"
service="$name.service"
timer="$name.timer"

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
\cp -R pyownet    /usr/local/lib/owlogger

# configuration
mkdir -p              /etc/owlogger
# cp -i owpost.toml     /etc/owlogger
cat > /etc/owlogger/$toml <<EOF
# owpost configuration file
# in TOML format https://toml.io/en/
# $name instance
#
# Normally resides in /etc/owlogger/$toml
# used for owpost.py
#
# See https://github.com/alfille/owlogger

# blank lines and text after '#' comments are ignored

# server location (external)
# usually a valid subdomain address
#server=owlogger.mypvs.net

# for testing if owlogger is running on same machine:
server="http://localhost:8001"

# owserver location (internal)
# Usually local and on well-known port
owserver="localhost:4304"

# name
# to distinguish multiple sources
# Choose a real, insightful name
name=$name

# Authentification token
# choose something better than this
token="simple_string"

# Temperature
# only one is needed and default is Fahrenheit
Fahenheit=true
# Celsius=true

# debugging output (for testing)
debug=false

# period in minutes
# better done in systemd or cron!
#period=15
EOF
chown -R $USER:$GROUP /etc/owlogger/$toml
chmod 660             /etc/owlogger/$toml

# script to run owlog_user
\cp owpost     /usr/bin
chmod +x       /usr/bin/owpost

# systemd files
cat > /etc/systemd/system/$service <<EOF
[Unit]
Description=Post 1-wire data from owserver to remote owlogger
Documentation=https://alfille.github.io/owlogger/owpost.html
${messages}After=owserver.service
${messages}Requires=owserver.service

[Service]
Type=oneshot
User=www-data
Group=www-data
# With configuration file in /etc/owlogger/
ExecStart=/usr/bin/python3 /usr/local/lib/owlogger/owpost.py --config /etc/owlogger/$toml
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/$timer <<EOF
[Unit]
Description=Run owpost ($name instance) periodically to send data to owlogger
Requires=$service

[Timer]
OnCalendar=*-*-* *:0/15:00
Persistent=true
Unit=$service

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable   $service
systemctl restart  $service
systemctl enable   $timer
systemctl restart  $timer
systemctl status --no-pager $service
systemctl status --no-pager $timer

echo "OWPOST install process finished"
echo "-------------------------------"
echo
