# Password protection

## Is password protection needed?

With [reverse-proxy protection](./reverse-proxy.md) and a [firewall](./firewall.md) data communication and storage is protected.

The only remaining issue is who can *read* your data?

## Web access

Without a paword, any =one who knows the URL (web address) can load the website and examine the sensor readings. The web access does not allow writing, nor reading files on the server.

So the question becomes, do I care who knows what readings are being stored? This divulges:

* Actual readings
* Historical readings
* Whether readings are currently being made

### No_password

Turning off password protection must be actively chosen. (Security by default).

* __owlogger.toml configuration__: `no_password=true`
* __owlogger.py command line__: `python3 /usr/local/lib/owlogger.py --no_password`

The command line takes precedence over the configuration file.

## Password protection

With the default password protection, username / passwords are stored in the database. The data cannot be viewed without valid credentials.

* Passwords are stored encrypted
* The [owlog_user.py](./owlog_user.md) program manages the usernames / passwords
* Users will be prompted to enter the password the first time accessing the data from a given location