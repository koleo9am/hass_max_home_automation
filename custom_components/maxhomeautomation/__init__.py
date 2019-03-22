"""MAX! Home Automation via HTTP API.

# Example configuration.yaml entry
maxhomeautomation:
  gateways:
    host: localhost
    port: 8080
    scan_interval: 10
    cubes:
      - cube_hex_address: 
        name: 
        radiator_thermostats:
          - hex_address:
            name: 
        wall_thermostats:
          - hex_address:
            name: 
        window_shutters:
          - hex_address:
            name: 
        eco_buttons:
          - hex_address:
            name: 


"""
import logging
import time
from socket import timeout
from threading import Lock

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
import json

from .consts import *

_LOGGER = logging.getLogger(__name__)

# DEFAULTS
DEFAULT_PORT = 8080
DEFAULT_METHOD = 'GET'
DEFAULT_SCAN_INTERVAL = 60

CONFIG_DEVICE = vol.Schema({
    vol.Required(CONF_HEX_ADDRESS): cv.string,
    vol.Required(CONF_NAME): cv.string,
})

CONFIG_CUBE = vol.Schema({
    vol.Required(CONF_HEX_ADDRESS): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_RADIATOR_THERMOSTATS, default={}):
            vol.All(cv.ensure_list, [CONFIG_DEVICE]),
    vol.Optional(CONF_WALL_THERMOSTATS, default={}):
            vol.All(cv.ensure_list, [CONFIG_DEVICE]),
    vol.Optional(CONF_WINDOWS_SHUTTERS, default={}):
            vol.All(cv.ensure_list, [CONFIG_DEVICE]),
    vol.Optional(CONF_ECO_BUTTONS, default={}):
            vol.All(cv.ensure_list, [CONFIG_DEVICE]),
})

CONFIG_GATEWAY = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default = DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SCAN_INTERVAL, default = DEFAULT_SCAN_INTERVAL): cv.time_period,
    vol.Required(CONF_CUBES, default={}):
            vol.All(cv.ensure_list, [CONFIG_CUBE]),
    
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_GATEWAYS, default={}):
            vol.All(cv.ensure_list, [CONFIG_GATEWAY]),
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Establish connection to MAX!HomeAutomation."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = config
        
    # Load platform parts
    load_platform(hass, 'climate', DOMAIN, {}, config)
    load_platform(hass, 'sensor', DOMAIN, {}, config)
    load_platform(hass, 'binary_sensor', DOMAIN, {}, config)

    # platform initialization was successful
    return True

class MaxHomeAutomationDeviceHandler:
    """Keep the cube instance in one place and centralize the update."""

    def __init__(self, gateway_base_url, cube_hex_address,  device_hex_address, scan_interval):
        """Initialize the Cube Handle."""
        # store initial values
        self._gateway_base_url = gateway_base_url
        self._cube_hex_address = cube_hex_address
        self._device_hex_address = device_hex_address
        self._scan_interval = scan_interval
        
        # MAX! Home Automation MAX! Cube JSON API URL
        device_data_url = self._gateway_base_url + "get-status-json?cube={}&device={}".format(self._cube_hex_address, self._device_hex_address)
        self._device_data_request = requests.Request(DEFAULT_METHOD, device_data_url).prepare()
                
        # JSON data initial value
        self.data = None
        
        # thread synchronization stuff
        self._mutex = Lock()
        # initially not actual 
        self._updatets = time.time() - self._scan_interval;

    def update(self):
        """Pull the latest data from the MAX! Home Automation."""
        # Acquire mutex to prevent simultaneous update from multiple threads
        with self._mutex:
            # Only update every update_interval
            if (time.time() - self._updatets) >= self._scan_interval:
                _LOGGER.debug("Updating")

                self._updatets = time.time()

                # fetch JSON data
                try:
                    with requests.Session() as sess:
                        # call-out
                        response = sess.send(self._device_data_request, timeout=10)
                        # process data
                        json_data = response.text
                        self.data = json.loads(json_data)
                        
                except Exception as ex:
                    _LOGGER.error("Max! Home Automation connection failed - Cube: {}, Device: {}, JSON data: {}".format (self._cube_hex_address, self._device_hex_address, ex))
                    self.data = None
                    # set next try to 60times scan interval
                    self._updatets = time.time() + (59 * self._scan_interval)
                    return False
                
            else:
                _LOGGER.debug("Skipping update")
    

class MaxHomeAutomationCubeHandler:
    """Keep the cube instance in one place and centralize the update."""

    def __init__(self, gateway_base_url, cube_hex_address,  scan_interval):
        """Initialize the Cube Handle."""
        # store initial values
        self._gateway_base_url = gateway_base_url;
        self._cube_hex_address = cube_hex_address;
        self._scan_interval = scan_interval
        
        # MAX! Home Automation MAX! Cube Duty URL
        cube_duty_url = self._gateway_base_url + "get-duty?cube={}".format(self._cube_hex_address)
        self._cube_duty_request = requests.Request(DEFAULT_METHOD, cube_duty_url).prepare()
        
        # JSON data initial value
        self.cube_duty = None
        
        # thread synchronization stuff
        self._mutex = Lock()
        # initially not actual 
        self._updatets = time.time() - self._scan_interval;

    def update(self):
        """Pull the latest data from the MAX! Home Automation."""
        # Acquire mutex to prevent simultaneous update from multiple threads
        with self._mutex:
            # Only update every update_interval
            if (time.time() - self._updatets) >= self._scan_interval:
                _LOGGER.debug("Updating")

                self._updatets = time.time()
                
                # fetch Duty data
                try:
                    with requests.Session() as sess:
                        # call-out
                        response = sess.send(self._cube_duty_request, timeout=10)
                        # process data
                        self.cube_duty = response.text
                        
                except Exception as ex:
                    _LOGGER.error("Max! Home Automation connection failed - Cube: {}, duty data: {}".format (self._cube_hex_address, ex))
                    self.cube_duty = None
                    # set next try to 60times scan interval
                    self._updatets = time.time() + (59 * self._scan_interval)
                    return False

            else:
                _LOGGER.debug("Skipping update")
