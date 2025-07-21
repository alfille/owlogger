# OWLOGGER

## What is it?

__owlogger__ is the external portion of the system. It stores data on the cloud, and displays it on a web page.

![owlogger2](owlogger2.png)

## Functional Details

* Written in python3, 
    * uses the http.server module for the web service
    * uses the sqlite3 module for database storage
* Data is stored in an SQL file
* Security comes from [reverse-proxy](./reverse-proxy.md) and [passwords](./password.md) 
* Only 3 files are recognized and served (for safety)

## Operational Details

__owlogger__ can be run directly by `python3 owpython.py` with options as needed, but it's easier to have database and configuration in [standard locations](./locations.md). 

The database must be in a location known to [__owlog_user__](./owlog_user.md) so that user/passwords can be managed.

Also, the port must match the reverse-proxied port of [__caddy__](./reverse-proxy.md)
