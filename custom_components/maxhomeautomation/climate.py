"""Support for MAX! Home Automation Thermostats via HTTP API."""
import logging

import requests
from socket import timeout

from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate import (
    STATE_AUTO, STATE_MANUAL, STATE_ECO, STATE_HEAT, 
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE,
    )
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from .consts import *
from .__init__ import MaxHomeAutomationDeviceHandler

from .consts import VERSION

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Iterate through all MAX! Devices."""

    devices = []
    
    # read configuration and setup platform
    gateways = hass.data[DATA_KEY][DOMAIN][CONF_GATEWAYS]
    for gateway in gateways:
        host = gateway[CONF_HOST]
        port = gateway[CONF_PORT]
        scan_interval = gateway[CONF_SCAN_INTERVAL].total_seconds()
        cubes = gateway[CONF_CUBES]
        gateway_url_base= "http://{}:{}/".format(host, port)

        # walk trough cubes
        for cube in cubes:
            # read config
            cube_address = cube[CONF_HEX_ADDRESS]
            cube_name = cube[CONF_NAME]
            radiator_thermostats = cube[CONF_RADIATOR_THERMOSTATS]
            wall_thermostats = cube[CONF_WALL_THERMOSTATS]
            window_shutters = cube[CONF_WINDOWS_SHUTTERS]
            eco_buttons = cube[CONF_ECO_BUTTONS]
        
            # walk trough radiator thermostats
            for radiator_thermostat in radiator_thermostats:
                device_address = radiator_thermostat[CONF_HEX_ADDRESS]
                device_name = radiator_thermostat[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationClimate (handler, device_name))
               
                            
            # walk trough wall thermostats
            for wall_thermostat in wall_thermostats:
                device_address = wall_thermostat[CONF_HEX_ADDRESS]
                device_name = wall_thermostat[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationClimate (handler, device_name))

    
    if devices:
        add_entities(devices)

    # platform initialization was successful
    return True

class MaxHomeAutomationClimate(ClimateDevice):
    """MAX! Home Automation ClimateDevice."""

    def __init__(self, device_handler, name):
        """Initialize MAX! Home Automation ClimateDevice."""
        self._name = name
        self._operation_list = [STATE_AUTO, STATE_MANUAL, STATE_HEAT, STATE_ECO]
        self._device_handler = device_handler
        
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def min_temp(self):
        """Return the minimum temperature - 4.5 means off."""
        return 4.5

    @property
    def max_temp(self):
        """Return the maximum temperature - 30.5 means on."""
        return 30.5

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        device = self._device_handler.data
        # device not found
        if device is None:
            return None
        # return the converted value
        return device.get(MHA_API_TEMPERATURE, None)

    @property
    def current_operation(self):
        """Return current operation (auto, manual, boost, vacation)."""
        device = self._device_handler.data
        # device not found
        if device is None:
            return None
        # return the converted value
        return MAP_MHA_OPERATION_MODE_HASS.get(device.get(MHA_API_MODE, None), None)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        device = self._device_handler.data
        # device not found
        if device is None:
            return None
        # return the converted value
        return device.get(MHA_API_SET_TEMPERATURE, None)

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is None:
            return False

        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        return self.set_max_home_automation_thermostat (self.current_operation, target_temperature)

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        return self.set_max_home_automation_thermostat (operation_mode, None)        

    def update(self):
        """Get latest data from MAX! Home Automation"""
        self._device_handler.update()
    
    def set_max_home_automation_thermostat (self, hass_operation_mode, temperature):
        import urllib.request
        
        command_url = self._device_handler._gateway_base_url + {
            STATE_AUTO: "set-automatic?cube={}&device={}{}".format(
                self._device_handler._cube_hex_address, self._device_handler._device_hex_address, 
                "" if temperature is None else "&temperature={}".format(temperature)),
            STATE_MANUAL: "set-manual?cube={}&device={}{}".format(
                self._device_handler._cube_hex_address, self._device_handler._device_hex_address, 
                "&temperature+=0.0" if temperature is None else "&temperature={}".format(temperature)),
            STATE_HEAT: "set-boost?cube={}&device={}".format(
                self._device_handler._cube_hex_address, self._device_handler._device_hex_address),
            # TODO vacation length as platform parameter or input
            STATE_ECO: "set-vacation?cube={}&device={}&eco&days=365".format(
                self._device_handler._cube_hex_address, self._device_handler._device_hex_address),
            }[hass_operation_mode]
        
        if command_url is None:
            return False
        
        _LOGGER.debug("MAX! Home Automation command to be called: {}".format(command_url))
        
        try:
            urllib.request.urlopen(command_url, timeout=10).read()
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error performing command: %s from %s failed with %s",
                self._request, self._request.url, ex)
            return False
        except timeout: 
            _LOGGER.error("Max! Home Automation command failed")
            return False
        
        return True

