# Firewall

Although not strictly needed for __owlogger__, good practice on any internet-accessible computer is to protect against incomming mesages with a firewall.

These are the requiremments and setting for the recommended setup with reverse-proxy and subdomains.

## owlogger system requirements

### owpost

* Only needs to initiate outgoing *tcp* connections on ports 80 (http) or 443 (https).
* owserver (the sensor source) is typically internal and within the forewall.

### owlogger

#### data feed

* From owpost
* https (port 443) to a reverse-proxied subdomain

#### TLS certificate

* source "Let's Encrypt"
* aquired and renewed by caddy
* needs *tcp* ports 80 and 443 open

### Web browser

* https (port 443) to a reverse-proxied subdomain

### Server management

Typically via __ssh__ using *tcp* port 22, although some cloud hosts have a web-based console interface.

## ufw

[uncomplicated firewall (ufw)](https://wiki.debian.org/Uncomplicated%20Firewall%20%28ufw%29) is easily installed on [ubuntu](https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-with-ufw-on-ubuntu) and debian

Typical configuration (as root or sudo for each line)

```
apt install ufw

ufw default deny incoming
ufw default allow outgoing

ufw allow ssh
ufw allow http
ufw allow https

ufw enable # say yes
ufw status
```

### Notes

1. Make sure you finish all these before logging out, or you may be locked out!
2. These settings will persist over server reboots
