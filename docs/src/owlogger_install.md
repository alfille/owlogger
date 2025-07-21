# owlogger install

## Debian / Ubuntu system

### Basic system:

```
# use "sudo" for each line unless you are root
sudo apt update
sudo apt upgrade
sudo apt install git python3 python3-jwt python-bcrypt
sudo apt install ufw caddy # optional but strongly recommended
```

### get owlogger software
```
git clone https://github.com/alfille/owlogger
```

### Install
```
cd owlogger/logger
. log_install.sh # The initial period is needed!
```

### Configure

See file [locations](./locations.md)

* owlogger
  * edit /etc/owlogger.toml
  * make sure token matches owpost
* owlog_user
  * Add any users / passwords
* caddy
  * edit /etc/caddy/Caddyfile
  * add reverse proxy for owlogger's subdomain

### example owlogger.toml
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

# No passwords? (for testing)
no_password=false

# debugging output (for testing)
debug=false
```

### From command line

Especially for testing
```
$ python3 logger/owlogger.py -h
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

