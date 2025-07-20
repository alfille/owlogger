# systemd

## What is it?

__systemd__ is the (newish) overall linux control program for managing programs and services (like web servers)

It handles:

* Starting services (like firewall and reverse proxy)
* Getting to sequence of program starts correct
* Running programs periodically if desired
* Restarting ptograms after errors
* Logging status and problems

More information on [Debian](https://wiki.debian.org/systemd)

---

### Basic systemd commands

* __status__
  * e.g. `systemctl status ufw.service` shows status of ufw (firewall)
  * Need to press Ctrl-C to exit
* __start__ | __stop__
  * e.g. `systemctl stop caddy.service` to stop caddy
  * __start__and __stop__ state do not persist after reboot
  * __stop__ will stop the service
  * __restart__ often can stop and start, but check status since not all services manage this well
* __enable__ | __disable__
  * e.g. `systemctl enable owserver`
  * sets the service to be started after every reboot
  * Also __start__ the service to get it started now, not just after a reboot
  * __disable__ to set the service to not start on reboot

---

## [ufw](./firewall.md) firewall

systemd files installed by default. No changes should be needed.

## [caddy](./reverse-proxy.md) reverse-proxy

systemd files installed by default. No changes should be needed.

## [owserver 1-wire server](./owserver.md)

systemd files installed by default.

Note that the default *owserver* configuration gives fake example sensors, so will need real hardware and configuration file changes (and __restart__ of the service__) to provide more than testing input.

---

## [owpost](./owpost.md)


For the local sensor-posting machine

The install script will add the following files to `/etc/systemd/system`

### Timer (owpost.timer)
```
[Unit]
Description=Run owpost periotically to send data to owlogger

[Timer]
OnBootSec=3min
OnActiveSec=15min
Unit=owpost.service

[Install]
WantedBy=timers.target
```

### Service (owpost.service)
```
[Unit]
Description=Post 1-wire data from owserver to remote owlogger
After=owserver.service
Requires=owserver.service

[Service]
Type=oneshot
# With configuration file in /etc/owlogger/owpost.toml
ExecStart=/usr/bin/python3 /usr/local/bin/owpost.py
# If no configuration file
# ExecStart=/usr/bin/python3 /usr/local/bin/owpost.py -o localhost:3504 -s https://remote.host:8001
```

---

1. configure owserver
2. start owserver
   
  * `systemctl enable owserver`
  * `systemctl start owserver`
  * `systemctl status owserver`
3. check owpost.toml file
4. start owpost
  * `systemctl enable owpost`
  * `systemctl start owpost`
  * `systemctl status owpost`

## [owlogger](./owlogger.md)


For the cloud server store and display program

The install script will add the following files to `/etc/systemd/system`

### Service (owlogger.service)
```
[Unit]
Description=OWLogger web server
After=network.target caddy.service
Requires=caddy.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/owlogger/owlogger.py 
WorkingDirectory=/usr/local/lib/owlogger
Restart=on-failure
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

---

1. [set up caddy](./reverse-proxy.md)
2. check owlogger.toml file
3. start owlooger
  * `systemctl enable owlogger`
  * `systemctl start owlogger`
  * `systemctl status owlogger`
4. [Set up users](./owlog_user.md) if password protection is desired
