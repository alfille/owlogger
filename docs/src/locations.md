# File locations

# Cloud server

## Database

```
/var/lib/owlogger/logger_data.db
```

## Programs and modules

```
/usr/local/lib/owlogger/owlogger.py
/usr/local/lib/owlogger/air-datepicker.js
/usr/local/lib/owlogger/air-datepicker.css
/usr/local/lib/owlogger/owlog_user.py

/usr/bin/owlogger
/usr/bin/owlog_user
```

## Configuration

```
/etc/owlogger/owlogger.toml
```

## systemd files

```
/etc/systemd/system/owlogger.service
/etc/systemd/system/owlogger.timer
```

## Caddyfile

```
/etc/caddy/Caddyfile
```

## Firewall

```
/etc/ufw/user.rules
/etc/ufw/user6.rules
```

## Repository copy
Depends on where git was run, but assuming you are root, in the `/root` directory:

```
/root/owlogger
```

## Installation script
```
/root/owlogger/logger/log_install.sh
```

# Sensor transmitter

## Program

```
/usr/local/lib/owlogger/owpost.py
/usr/bin/owserver
```

## Configuration

```
/etc/owlogger/owpost.toml
/etc/owfs.conf
```

## systemd files

```
/etc/systemd/system/owlogger.service
/etc/systemd/system/owserver.service
```
## Repository copy
Depends on where git was run, but assuming you are root, in the `/root` directory:

```
/root/owlogger
```
## Installation script
```
/root/owlogger/post/log_install.sh
```




