# Security

## General Notes

_owlogger_ is a systems of components, so the security aspect needs to be analyzed in parts. In general, this collects low-value data, so collateral damage is a consideration.

## Programs

Best practice:

![owlogger2](owlogger2.png)

### owserver

Well tested. Read-only of data from physical sensors. communication is via *owserver protocol* but typically will be internal to the posting station.

### owpost

Send-only externally, potentially via *https* if a reverse proxy is employed.

### owlogger

Uses *http.server* python module, which is advertised as _not_ hardened. The accepted HTTP messages are restricted, specifically no arbitrary file reading or external program use. Using a reverse proxy to keep communication internal is advisable, however.

### Browser

Data on the display device is performed via *HTML* with a non-persistent javascript component. The [air-datepicker](https://github.com/t1m0n/air-datepicker) module is used, but not loaded from an external source.

## Logging data

### Encryption

Data is sent in clear text via *http* by default. Using *https* by adding a proxy agent (e.g. _caddy_) to the server is easily accomplished and implementation of that scheme is detailed.

### Injection

All data is logged by default, potentially including malicious spam. A simple form of authentification using an arbitrary text string (_token_) is available. This only makes sense if the traffic is also encrypted. This token must be added at both ends at startup and requires that both ends are secure from inspection.

## Access to data

Access (to owlogger web display) is read-only, but web-available -- the point of the system. Communication is via *http* by default.

### Encryption

*https* (TLS encryption) is easily added with a proxy agent (e.g._caddy_) and implementation of that is encouraged and detailed with design and scripts.

### Authentification

Authetification for access is not implemented.

## Database

The database is stored on the server, and so requires that the server's file system is not compromised. 

* Data entry is via sqlite3 with protection against SQL injection attack
* Data is managed in a write-only mode
* There is a potential for spam data to be sent to the system, filling up the file space (see tokens).


## Physical

Phyisical access, compromise and damage is generally out of scope.

### data collectors

Sensors, wires and the _owputter_ component may be in a vulnerable area to intentional or unintentional damage, so robust installation is advisable. These components are generally inexpensive, fortunately.
