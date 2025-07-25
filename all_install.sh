#!/bin/sh
# Use /bin/sh for maximum portability across POSIX-compliant shells

# File for setting up internal transmitter component of owlogger
# must be run as root (e.g. sudo)

# Check if the script is run as root

# Check if the effective user ID is 0 using the 'id -u' command
if [ "$(id -u)" -ne 0 ]; then
  echo "Error: This script must be run as root or with sudo." >&2
  # Try to suggest how to run it if sudo is available and the user isn't already root
  if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then
    echo "Please run: sudo \"$0\" \"$@\"" >&2
  fi
  exit 1
fi

# logger
cd logger
sh ./log_install.sh
cd ..

# post
cd post
sh ./post_install.sh
cd ..
