# OWLOG_USER

## Purpose

__owlog_user__ manages usernames and passwords for web access to __owlogger__.

## Command line

__owlog_user__ is a command line program that runs on the same computer as __owlogger__.

* Same configuration file: `/etc/owlogger/owlogger.toml`
* Same sqlite3 database: `/var/lib/owlogger/logger_data.db`
* Same location for the python file: `/usr/local/lib/owlogger/owlog_user.py`
* The installation script creates `owlog_user` in `/usr/bin` as an easier was to run the program

### Options

```
usage: owlog_user.py [-h] [--config [CONFIG]] [-f [DATABASE]] [-l] [-r] username

Add users and passwords to database for `owlogger` security

positional arguments:
  username              Username to add, update or remove

options:
  -h, --help            show this help message and exit
  --config [CONFIG]     Location of any configuration file. Optional default=/etc/owlogger/owlogger.toml
  -f [DATABASE], --file [DATABASE]
                        database file location (optional) default=./logger_data.db
  -l, --list            List users registered in database
  -r, --remove          Remove user from this database

Repository: https://github.com/alfille/owlogger
```

### Adding/updating a user

```
$ owlog_user paul
Password for paul: 
```

Note:

* Passwords are store encrypted (bcrypt) in the database
* Passwords cannot be retrieved, only overwritten.
* There are no restrictions on password content
* usernames must be unique
* Use quotation marks if username containes spaces. e.g.: `owlog_user "paul alfille"

### Listing users

```
$ sudo owlog_user --list
paul
paul alfille
```

### Remove a user

```
$ owlog_user -r paul

$ owlog_user -l
paul alfille
```

## Implementation (informational, not important)

The database has a `userlist table`

```
sqlite> .dump userlist
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE userlist (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            );
INSERT INTO userlist VALUES('paul alfille','$2b$12$x81g2MvcVs2TogTKKy5sjuPCTwiaQ2y9kTeVljDgOvOg9fcm8hh2i');
COMMIT;
```


