"""Support for MAX! Home Automation Thermostats Sensors."""
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.const import TEMP_CELSIUS
from .__init__ import (
    DATA_KEY, MHA_API_DEVICES, MHA_API_ADDRESS, MHA_API_NAME, 
    MHA_API_RADIATOR_THERMOSTAT, MHA_API_TYPE, MHA_API_TEMPERATURE,
    MHA_API_SET_TEMPERATURE, MHA_API_VALVE, MHA_API_OFFSET
    )

_LOGGER = logging.getLogger(__name__)

# sensor type constants
MHA_SENSOR_TYPE_TEMPERATURE = MHA_API_TEMPERATURE
MHA_SENSOR_TYPE_SET_TEMPERATURE = MHA_API_SET_TEMPERATURE
MHA_SENSOR_TYPE_VALVE = MHA_API_VALVE
MHA_SENSOR_TYPE_OFFSET = MHA_API_OFFSET

# allowed sensors types
MHA_ALLOWED_SENSOR_TYPES = [
    MHA_SENSOR_TYPE_TEMPERATURE, 
    MHA_SENSOR_TYPE_SET_TEMPERATURE, 
    MHA_SENSOR_TYPE_VALVE, 
    MHA_SENSOR_TYPE_OFFSET,
    ]

# map sensor type to unit
MHA_UNIT_HA_CAST = {
    MHA_SENSOR_TYPE_TEMPERATURE: TEMP_CELSIUS,
    MHA_SENSOR_TYPE_SET_TEMPERATURE: TEMP_CELSIUS,
    MHA_SENSOR_TYPE_VALVE: '%',
    MHA_SENSOR_TYPE_OFFSET: TEMP_CELSIUS,
}

# map sensor type to icon
MHA_ICON_HA_CAST = {
    MHA_SENSOR_TYPE_TEMPERATURE: 'mdi:thermometer',
    MHA_SENSOR_TYPE_SET_TEMPERATURE: 'mdi:thermometer',
    MHA_SENSOR_TYPE_VALVE: 'mdi:radiator',
    MHA_SENSOR_TYPE_OFFSET: 'mdi:delta'
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Iterate through all MAX! Devices and add sensors from termostats."""
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
                    MaxHomeAutomationSensor (handler, device_name + " - Temperature", device_address, MHA_SENSOR_TYPE_TEMPERATURE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Target Temperature", device_address, MHA_SENSOR_TYPE_SET_TEMPERATURE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Valve", device_address, MHA_SENSOR_TYPE_VALVE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Offset", device_address, MHA_SENSOR_TYPE_OFFSET))
                                
    add_entities(devices)


class MaxHomeAutomationSensor(Entity):
    """Representation of a Max! Home Automation sensor."""
    
    def __init__(self, cubehandle, name, device_address, sensor_type):
        """Initialize the sensor."""
        # check sensor_type
        if sensor_type not in MHA_ALLOWED_SENSOR_TYPES:
            raise ValueError("Unknown Max! Home Automation sensor type: {}".format(sensor_type))
        # store values
        self._cubehandle = cubehandle
        self._name = name
        self._sensor_type = sensor_type
        self._device_address = device_address
        self._state = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return MHA_UNIT_HA_CAST.get(self._sensor_type, None)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return MHA_ICON_HA_CAST.get(self._sensor_type, None)
    
    def update(self):
        """Get latest data from MAX! Home Automation"""
        self._cubehandle.update()
        # find the device
        device = self._cubehandle.device_by_address(self._device_address)
        # update internal values
        self._state = device[self._sensor_type]