# Credit and Acknowledgment

__owlogger__ is a system os several components, and uses several open-source componets:

## Python

Python3, and many modules:

 * The standard lib: argparse, datetime, http.server, io.BytesIO, json, math, os, sys, time, urllib, urllib.parse
 * The requests module
 * A version of [pyownet](https://github.com/miccoli/pyownet) by Stefanno Micccoli mildly modified
   * update to Python3
   * use f-string formatting
   * included directly in the owlogger repository

## owserver

Part of the [owfs -- 1-wire file system](https://github.com/owfs/owfs) maintained by a small community

## 1-wire

![8130](8130.gif)

1-wire is a simple protocol for communication with external enumerated devices, like memory, temperature and voltage. The protocol actually uses 2 wires, but data and power are combined on a simegle line that multiple sensors can share. Originally Designed by Dallas Semiconductor, it's now  produt of [Analog Devices](https://www.analog.com/en/product-category/1wire-devices.html)

## Javascript

Basic code is embeddd in __owlogger__ but a nice calendar function comes from [air-datepicker](https://github.com/t1m0n/air-datepicker) by T1m0n (Timofey).

The air-datepicker code is slightly modified to default to english text and hosted directly in this repository.

## caddy

Best practice is to use a reverse-proxy in frnt of __owlogger__ likw [caddy](https://github.com/caddyserver/caddy) by Matt Holt

## firewall

[ufw](https://github.com/caddyserver/caddy) is used by Debian and Ubuntu and helps limit external attacks.
