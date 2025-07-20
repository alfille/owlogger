# File locations

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
```

## Configuration

```
/etc/owlogger/owlogger.toml
```

## systemd files

```
/etc/systemd/system/owlogger.server
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

## Repository
Depends on where git was run, but assuming you are root, in the `/root` diurectory:

```
/root/owlogger
# Installation script
/root/owlogger/logger/log_install.sh
```
