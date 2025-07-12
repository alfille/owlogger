# owlogger install

## Debian / Ubuntu system

### Basic system:

```
# use "sudo" for each line unless you are root
sudo apt update
sudo apt upgrade
sudo apt install git python3 python3-jwt
```

### get owlogger software
```
git clone https://github.com/alfille/owlogger
```

## Choose either Recommended (secure) or Basic (testing, insecure)

----

## Recommended secure setup
```
sudo apt install python3-jwt caddy ufw
cd owlogger/logger
sudo . /logger_install.sh
```

---

## Insecure basic setup
```
cd owlogger/logger
sudo . /logger_basic.sh
```


