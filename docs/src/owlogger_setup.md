# owlogger setup

## Functions

__OWLogger__ has 3 functions:

* Accept data from __OWPost__
* Store data in a database
* Server the data to the web

---

## Security

Additionally, there are security options for each function:

* JWT tagging of incoming data to ensure provenance
* reverse-proxy TLS layer to communications
* password gating of web access

---

## Command line options

```
usage: owlogger [-h] [--config [CONFIG]] [-s [SERVER]] [-t [TOKEN]] [-f [DATABASE]] [-d] [--no_password]

Logs 1-wire data to a database that can be viewed on the web. Works with 'owpost' and 'generalpost'

options:
  -h, --help            show this help message and exit
  --config [CONFIG]     Location of any configuration file. Optional default=/etc/owlogger/owlogger.toml
  -s [SERVER], --server [SERVER]
                        Server IP address and port (optional) default=localhost:8001
  -t [TOKEN], --token [TOKEN]
                        Optional authentification token (text string) to match with owpost or generalpost. JWT secret.
  -f [DATABASE], --file [DATABASE]
                        database file location (optional) default=./logger_data.db
  -d, --debug           Print debugging information
  --no_password         Turns off password protection

Repository: https://github.com/alfille/owlogger
```

---

## Config file [TOML format](https://toml.io/en/)

__/etc/owlogger/owlogger.toml__

```
# owlogger configuration file
# in TOML format https://toml.io/en/
#
# Normally resides in /etc/owlogger/owserver.toml
# used for owlogger.py and owlog_user.py
#

# this server location
#  for reverse-proxy protection (caddy)
server="http://localhost:8001"

# database for logging (sqlite3 format)
database="/var/lib/owlogger/logger_data.db"

# bypass passwo# Authentification token
token="simple_string"

rds? (for testing)
no_password=false

# debugging output (for testing)
debug=false
```

---

## systemd service file

__/etc/systemd/system/owlogger.service__

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

Note that configuration comes from the TOML configuration file rather than the command line

---
## Reverse proxy Caddyfile setup

---
### Simple -- no other web services on the server

Here is a simple and complete Caddyfile to reverse-proxy a service running on port 8001. Caddy will automatically handle the TLS certificate for you.

Code snippet

```
# Caddyfile
#
# Replace "your-domain.com" with your actual domain name.

your-domain.com {
    # Forward all traffic to the local service running on port 8001
    reverse_proxy localhost:8001
}
```

### How It Works
your-domain.com { ... }: This is a site block. Caddy will listen for requests to your-domain.com.

Automatic HTTPS: Because you provided a public domain name, Caddy automatically enables HTTPS, gets a TLS certificate from Let's Encrypt, and renews it for you. There is no extra configuration needed.

reverse_proxy localhost:8001: This is the core directive. It tells Caddy to forward all incoming web traffic to the service running on the same machine (localhost) at port 8001.

How to Use It
Replace the Domain: Edit the file and change your-domain.com to your actual domain.

DNS Record: Make sure your domain's A or AAAA DNS record points to the public IP address of the server where Caddy is running.

Firewall: Ensure your server's firewall allows traffic on ports 80 (for the HTTP challenge) and 443 (for HTTPS).

caddy run
Caddy will start, acquire the certificate, and begin serving your site over HTTPS.

---
### More complex, more than one service

Here is a Caddyfile that reverse-proxies two different services, with Caddy automatically handling TLS certificate acquisition and renewal.

Code snippet

```
# Caddyfile
#
# Replace the domain names and backend ports with your actual values.

service1.example.com {
    # Forwards traffic from service1.example.com to a local service on port 8080
    reverse_proxy localhost:8080
}

owlogger.example.com {
    # Forwards traffic from owlogger.example.com to a different local service on port 8001
    reverse_proxy localhost:8001
}
```

### How It Works

* Automatic TLS: Caddy automatically provisions and renews TLS certificates from Let's Encrypt for any site defined with a public domain name (like service1.example.com). 
  * You don't need to add any special TLS directives.
* Site Blocks: Each service is defined in its own block, starting with the domain name.
* reverse_proxy: This directive tells Caddy to forward all incoming requests for that domain to the specified backend address (ip:port).

### How to Use

Create a file named Caddyfile with the content above.

Make sure your two services are running (e.g., one on port 8080, the other (owlogger) on 8001).

### Prerequisites
For automatic TLS to work, you must have:

* DNS Records: An A or AAAA DNS record for both service1.example.com and service2.example.com pointing to your Caddy server's public IP address.
* Firewall Ports: Your server's firewall must allow inbound traffic on ports 80 and 443. Caddy uses port 80 for the TLS certificate challenge and port 443 for HTTPS traffic.
*