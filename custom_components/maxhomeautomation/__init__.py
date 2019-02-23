"""MAX! Home Automation via HTTP API.

# Example configuration.yaml entry
maxhomeautomation:
  gateways:
    - host: localhost
      port: 8080
      scan_interval: 10


"""
import logging
import time
from socket import timeout
from threading import Lock

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.components.climate import (
    STATE_AUTO, STATE_MANUAL, STATE_ECO, STATE_HEAT
    )
import json

_LOGGER = logging.getLogger(__name__)

# PLATFORM CONSTS
DOMAIN = 'maxhomeautomation'
DATA_KEY = 'maxhomeautomation'
NOTIFICATION_ID = 'maxhomeautomation_notification'
NOTIFICATION_TITLE = 'Max!HomeAutomation HTTP gateway setup'

# DEFAULTS
DEFAULT_PORT = 8080
DEFAULT_METHOD = 'GET'
DEFAULT_SCAN_INTERVAL = 60

#API_CONSTS
MHA_API_DEVICES = 'devices'
MHA_API_ADDRESS = 'address'
MHA_API_NAME = 'name'
MHA_API_TYPE = 'type'
MHA_API_TEMPERATURE = 'temperature'
MHA_API_SET_TEMPERATURE = 'set_temperature'
MHA_API_MODE = 'mode'
MHA_API_VALVE = 'valve'
MHA_API_OFFSET = 'offset'
MHA_API_ERROR = 'error'
MHA_API_INITIALIZED = 'initialized'
MHA_API_BATTERY = 'battery_low'
MHA_API_PANEL_LOCKED = 'panel_locked'
MHA_API_LINK_ERROR = 'link_error'
MHA_API_OPEN = 'open'

MHA_API_RADIATOR_THERMOSTAT = 'radiator thermostat'
MHA_API_SHUTTER_CONTACT = 'shutter contact'
MHA_API_ECO_BUTTON = 'eco button'

MHA_STATE_AUTOMATIC = 'automatic'
MHA_STATE_MANUAL = 'manual'
MHA_STATE_BOOST = 'boost'
MHA_STATE_VACATION = 'vacation'

MAP_MHA_OPERATION_MODE_HASS = {
    MHA_STATE_AUTOMATIC: STATE_AUTO,
    MHA_STATE_MANUAL: STATE_MANUAL,
    MHA_STATE_BOOST: STATE_HEAT,
    MHA_STATE_VACATION: STATE_ECO,
    }

#SCHEMA
CONF_GATEWAYS = 'gateways'

CONFIG_GATEWAY = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default = DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SCAN_INTERVAL, default = DEFAULT_SCAN_INTERVAL): cv.time_period,
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
        hass.data[DATA_KEY] = {}

    connection_failed = 0
    gateways = config[DOMAIN][CONF_GATEWAYS]
    for gateway in gateways:
        host = gateway[CONF_HOST]
        port = gateway[CONF_PORT]
        scan_interval = gateway[CONF_SCAN_INTERVAL].total_seconds()
        gateway_url_base= "http://{}:{}/".format(host, port)

        try:
            import urllib.request
            
            #Get space separated list of cubes via http://<max-home-automation>/get-cubes-list
            cubes_list_url = gateway_url_base + "get-cubes-list"
            cubes = urllib.request.urlopen(cubes_list_url).read()
            for cube_address in cubes.split ():
                # create handler for MAX! Cube via MAX! Home Automation JSON API
                cube_hex_address = cube_address.decode('UTF-8')
                handler = MaxHomeAutomationHandler(gateway_url_base, cube_hex_address, scan_interval)
                hass.data[DATA_KEY][cube_hex_address] = handler
                
        except Exception as ex:
            _LOGGER.error("Unable to connect to Max!HomeAutomation gateway: %s", str(ex))
            hass.components.persistent_notification.create(
                'Error: {}<br />'
                'You will need to restart Home Assistant after fixing.'
                ''.format(ex),
                title = NOTIFICATION_TITLE,
                notification_id = NOTIFICATION_ID)
            connection_failed += 1

    if connection_failed >= len(gateways):
        return False

    # Load platform parts
    load_platform(hass, 'climate', DOMAIN, {}, config)
    load_platform(hass, 'sensor', DOMAIN, {}, config)
    load_platform(hass, 'binary_sensor', DOMAIN, {}, config)

    # platform initialization was successful
    return True


class MaxHomeAutomationHandler:
    """Keep the cube instance in one place and centralize the update."""

    def __init__(self, gateway_base_url, cube_hex_address,  scan_interval):
        """Initialize the Cube Handle."""
        # store initial values
        self._gateway_base_url = gateway_base_url;
        self._cube_hex_address = cube_hex_address;
        self._scan_interval = scan_interval
        
        # MAX! Home Automation MAX! Cube JSON API URL
        cube_data_url = self._gateway_base_url + "get-status-json?cube={}".format(self._cube_hex_address)
        self._cube_data_request = requests.Request(DEFAULT_METHOD, cube_data_url).prepare()
        
        # JSON data initial value
        self._cube_json = None
        
        # thread synchronization stuff
        self._mutex = Lock()
        # initialy not actual 
        self._updatets = time.time() - self._scan_interval;

    def update(self):
        """Pull the latest data from the MAX! Home Automation."""
        # Acquire mutex to prevent simultaneous update from multiple threads
        with self._mutex:
            # Only update every update_interval
            if (time.time() - self._updatets) >= self._scan_interval:
                _LOGGER.debug("Updating")

                try:
                    with requests.Session() as sess:
                        # callout
                        response = sess.send(self._cube_data_request, timeout=10)
                        # process data
                        data = response.text
                        self._cube_json = json.loads(data)
                        
                except requests.exceptions.RequestException as ex:
                    _LOGGER.error("Error fetching data: %s from %s failed with %s",
                        self._request, self._request.url, ex)
                    self._cube_json = None
                    return False
                except timeout:
                    _LOGGER.error("Max! Home Automation connection failed")
                    self._cube_json = None
                    return False

                self._updatets = time.time()
            else:
                _LOGGER.debug("Skipping update")
                
    def device_by_address(self, device_address):
        """Find device from MAX! Home Automation data"""
        for device in self._cube_json[MHA_API_DEVICES]:
            if device_address == device[MHA_API_ADDRESS]:
                return device
        return None
    
    @staticmethod
    def encode_device_address (device_address):
        """Converts numeric device address to 6-digit HEX."""
        return '{0:0{1}X}'.format(device_address,6)
    
    @staticmethod
    def map_temperature_mha_to_hass (mha_temperature):
        """Map Temperature from MAX! Home Automation to HASS."""
        if mha_temperature is None:
            return 0.0
        return mha_temperature
