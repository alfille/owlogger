# Credit and Acknowledgment

__owlogger__ is a system of multiple components, and leverages several open-source projects:

## Python

Python3, and many modules:

 * The standard lib: argparse, datetime, http.server, io.BytesIO, json, math, os, sys, time, urllib, urllib.parse
 * Also the standard database module: sqlite3 
 * The requests module for sending data to a remote server

## pyownet

 * [pyownet](https://github.com/miccoli/pyownet) by Stefanno Micccoli is  python module that communicates directly woth owserver. The version here is slightly modified.
   * update to Python3
   * use f-string formatting
   * included directly in the owlogger repository

## owserver

Part of the [owfs -- 1-wire file system](https://github.com/owfs/owfs) maintained by a group of developers.

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

## sqlite3

The database used is the [sqlite3 library](https://sqlite.org/index.html) by D Richard Hipps. Not only is it imbedded in python, but it can be used as stand-alone program on the database file.

## mdbook

This documentation on owlogger os arranged using [mdbook](https://docs.rs/mdbook/latest/mdbook/index.html) -- a documentation system from the Rust Language project.
