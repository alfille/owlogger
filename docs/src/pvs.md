# Virtual Private Server (VPS)

## What is it

Available from many vendors, a PVS is esssentially what appears to be a dedicated bare-metal computer in the cloud that is actually a guest client in a server farm.

Typically you will get:

* root access
* dedicated IP address
* easily installed base operating system (debian, ubuntu, freebsd, etc)
* defined services:
  * disk space
  * network bandwidth
  * cpu(s)
  * ram
  * management console (for starting, resetting

Other services, like domain registration, ecommerce software, and backups may be available at added cost

## Examples:

* [Kamatera](https://www.kamatera.com/solutions/vps-hosting/) start at $4/mo for 1CPU, 20G disk, 1G ram, 5TB/mo network -- more than enough for __owlogger__ with other applications as well. This is what I use.
* [Ionis](https://www.ionos.com/servers/vps) as little as $2/month with different options 
* [Hotinger](https://www.hostinger.com/vps-hosting) $5/mo with similar resources

## Caveates

Many offers for "servers" or "web sites" do not give root access which limits your ability to add software (like owlogger). They are designed as a turnkey small business website for non-technical users and limit choices to reduce problems and support costs.

## In practice

1. Select base operating system, username and password
2. Start server
3. Note IP address
4. Test access via ssh and update software
5. Get a [domain](./domain.md)
  * Will need subdomains like owlogger.domain.name 
6. Install software (git ufw caddy owlogger)
7. Configure and start owlogger service

