# Requirements

## Hardware

* 1-wire sensors
* a transmitting computer (like a Raspberry Pi)
* an [external computer](./cloudserver.md) (or [virtual private server](./pvs.md))) to store data and provide web access

## Services

* A [Domain](./domain.md)
* root access to your cloud server

## Software

* Operating system -- linux is tested and described
* [owlogger](https://github.com/alfille/owlogger) programs
* [owserver](./owserver.md) for one-wire
* Python3 with some modules
* [Firewall](./firewall.md) and [reverse-proxy](./reverse-proxy.md)

Note: the software is free and easily install using Debian or Ubuntu flavors of linux
