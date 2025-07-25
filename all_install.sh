#!/usr/bin/env bash
# File for setting up internal transmitter component of owlogger
# must be run as root (e.g. sudo)

# Check if the script is run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ This script must be run as root. Try using sudo."
  exit 1
fi

# logger
cd logger
sh log_install.sh
cd ..

# post
cd post
sh post_install.sh
cd ..
