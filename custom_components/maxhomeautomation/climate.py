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
from .__init__ import (
    DATA_KEY, MHA_API_DEVICES, MHA_API_ADDRESS, MHA_API_NAME, 
    MHA_API_RADIATOR_THERMOSTAT, MHA_API_TYPE, MHA_API_TEMPERATURE,
    MHA_API_MODE, MHA_API_SET_TEMPERATURE, MAP_MHA_OPERATION_MODE_HASS
    )
from .__init__ import MaxHomeAutomationHandler

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Iterate through all MAX! Devices and add thermostats."""
    if discovery_info is None:
        return

    devices = []
    for handler in hass.data[DATA_KEY].values():
        handler.update()
        # walk through devices
        for device in handler._cube_json[MHA_API_DEVICES]:
            #we have thermostat
            if device[MHA_API_TYPE] == MHA_API_RADIATOR_THERMOSTAT:
                device_address = device[MHA_API_ADDRESS]
                device_name = device[MHA_API_NAME]
                
                devices.append(
                    MaxHomeAutomationClimate (handler, device_name, device_address))

    if devices:
        add_entities(devices)

class MaxHomeAutomationClimate(ClimateDevice):
    """MAX! Home Automation ClimateDevice."""

    def __init__(self, cubehandler, name, device_address):
        """Initialize MAX! Home Automation ClimateDevice."""
        self._name = name
        self._operation_list = [STATE_AUTO, STATE_MANUAL, STATE_HEAT, STATE_ECO]
        self._device_address = device_address
        self._cubehandle = cubehandler
        
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
        device = self._cubehandle.device_by_address(self._device_address)

        # Map and return current temperature
        return MaxHomeAutomationHandler.map_temperature_mha_to_hass(device[MHA_API_TEMPERATURE])

    @property
    def current_operation(self):
        """Return current operation (auto, manual, boost, vacation)."""
        device = self._cubehandle.device_by_address(self._device_address)
        return MAP_MHA_OPERATION_MODE_HASS[device[MHA_API_MODE]]

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        device = self._cubehandle.device_by_address(self._device_address)
        return MaxHomeAutomationHandler.map_temperature_mha_to_hass(device[MHA_API_SET_TEMPERATURE])

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
        self._cubehandle.update()
    
    def set_max_home_automation_thermostat (self, hass_operation_mode, temperature):
        import urllib.request
        
        command_url = self._cubehandle._gateway_base_url + {
            STATE_AUTO: "set-automatic?cube={}&device={}{}".format(
                self._cubehandle._cube_hex_address, MaxHomeAutomationHandler.encode_device_address(self._device_address), 
                "&temperature={}".format if temperature else ""),
            STATE_MANUAL: "set-manual?cube={}&device={}{}".format(
                self._cubehandle._cube_hex_address, MaxHomeAutomationHandler.encode_device_address(self._device_address), 
                "&temperature+=0.0" if temperature is None else "&temperature={}".format(temperature)),
            STATE_HEAT: "set-boost?cube={}&device={}".format(
                self._cubehandle._cube_hex_address, MaxHomeAutomationHandler.encode_device_address(self._device_address)),
            # TODO vacation length as platform parameter or input
            STATE_ECO: "set-vacation?cube={}&device={}&eco&days=365".format(
                self._cubehandle._cube_hex_address, MaxHomeAutomationHandler.encode_device_address(self._device_address)),
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

