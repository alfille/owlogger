# Reverse-proxy

## What is it?

A *reverse proxy* takes incoming external connections and sends them to an internal service. In this case, the external connections are HTTPS protected, but the internal ones are not.

![owlogger2](owlogger2.png)

## [caddy](https://caddyserver.com/)

Caddy is a well documented web server (like Apache or Ngnix). Advantages:

1. Built-in support for free TSL certificates (via [Lets Encrypt](https://letsencrypt.org/))

  * Aquires certificates automatically
  * Renews certificates automatically
  
2. Relatively light resources
3. Well documented
4. Simple configuration file 


### Caddyfile

Here is an example, using subdomains:

* Main web server: file hosting from a specific directory root
* Proxied couchdb access
* Proxied owlogger access

```
alfille.online {
        root * /srv/potholder
        encode gzip zstd
        file_server
}

couchdb.alfille.online
        reverse_proxy localhost:5984
}

owlogger.alfille.online {
        reverse_proxy localhost:8001
}
```

So Caddy serves as a protective intermediary, requiring all external access to owlogger be TSL protected

---

### Installation

