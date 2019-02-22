# hass_max_home_automation
Home Assistant support for MAX! Cube via MAX! Home Automation - HTTP API

## Sample configuration
```yaml
# Example configuration.yaml entry
maxhomeautomation:
  gateways:
    - host: localhost
      port: 8080
      scan_interval: 10
```
## Conditions
Feel free to use. Feel free to make Pull requests with enhanced features or correction of bugs.
Please note I have started with Home Assistant and MAX! Cube system on 02/15/2019. 
Hence this implementation is probably not following HA best practices.

As almost everyone I am developing this in my free time, so be kind in case I have delays in communication/enhancements.

## Deployment
I have Home Assistant and MAX! Home Automation installed on the same Raspberry PI Model 3B+.
MAX! Home Automation has enabled HTTP API only for localhost at 8080 port.

## Useful links
How to install MAX! Home Automation on Raspberry PI: https://sourceforge.net/p/max-home-automation/wiki/Raspberry%20installation/

## Feature list
* Climate Component
  * all Operational modes: AUTO, MANUAL, BOOST, VACATION
  * Vacation via ECO mode - fixed vacation length 365 days 
* Sensors (yet only for thermostatic valves)
  * current temperature
  * target temperature
  * valve
  * offset
* Binary Sensors (yet only for thermostatic valves)
  * Link Error
  * Error
  * Low Battery
  * Panel Locked
  * Initialized

## Planned Features
* Support for Window Sensor
* Support for Eco button
* Support for Wall Thermostat (I have no hardware one to test)

