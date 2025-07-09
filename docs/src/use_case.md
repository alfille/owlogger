# USE CASE

![owlogger](owlogger.png)

## Basic premise

* Internal sensor readings to be monitored
* Internal network should not allow __incoming__ access. Why?
  * Dynamic IP addresses are not a problem
  * Better security
  * Comply with facility policy
* An external server is available
* Simple web viewing from any device

## Some monitoring scenarios:

* Aquarium
* Beer brewing
* Wine cellar
* Pipes freezing
* Chicken coop

## Types of data

### 1-wire sensors

__owpost__ is designed specifically for 1-wire temperature and humidity

### Other logging

__generalpost__ posted any arbitray text string to the logging database

