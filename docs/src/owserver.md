# owserver

[owserver](https://owfs.org/uploads/owserver.html) is part of the __One Wire File System__.

It connects to 1-wire controllers (of almost any kind) and transmits reading over the network using a special protocol.

Although the original (very complete) documentation is availble on the [old site](https://owfs.org/index_php_page_owserver_protocol.html), current development is [here](https://github.com/owfs/owfs).

## Installation

### debian or ubuntu

```
apt install owserver
```

### RPM (fedora, suse, redhat..)


package `owfs-server``

### Source

C program needs standard autoconf automake, etc

## Configuration

owserver will run as a systemd service (althoug it can run directly from the command line)

Configuration at `/etc/owfs.config`

## Typical steps:

1. attach a 1-wire device
2. install owserver
  * `apt install owserver` 
3. edit `/etc/owfs.conf` to match your setup
  * server address `localhost:4304`
  * device type (usb, serial, w1, etc) 
4. Start service
```
systemctl start owserver
systemctl enable owserver
systemctl status owserver
```
5. Testing:
```
apt install owshell
owdir -s localhost:4304
```

