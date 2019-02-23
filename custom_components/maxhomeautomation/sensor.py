"""Support for MAX! Home Automation Thermostats Sensors."""
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.const import TEMP_CELSIUS
from .__init__ import (
    DATA_KEY, MHA_API_DEVICES, MHA_API_ADDRESS, MHA_API_NAME, 
    MHA_API_RADIATOR_THERMOSTAT, MHA_API_TYPE, MHA_API_TEMPERATURE,
    MHA_API_SET_TEMPERATURE, MHA_API_VALVE, MHA_API_OFFSET,
    MHA_API_ECO_BUTTON, MHA_API_MODE, MAP_MHA_OPERATION_MODE_HASS
    )

_LOGGER = logging.getLogger(__name__)

# sensor type constants
MHA_SENSOR_TYPE_TEMPERATURE = MHA_API_TEMPERATURE
MHA_SENSOR_TYPE_SET_TEMPERATURE = MHA_API_SET_TEMPERATURE
MHA_SENSOR_TYPE_VALVE = MHA_API_VALVE
MHA_SENSOR_TYPE_OFFSET = MHA_API_OFFSET
MHA_SENSOR_TYPE_ECO_BUTTON = MHA_API_MODE
MHA_SENSOR_TYPE_DUTY = 'duty'

# allowed sensors types
MHA_ALLOWED_SENSOR_TYPES = [
    MHA_SENSOR_TYPE_TEMPERATURE, 
    MHA_SENSOR_TYPE_SET_TEMPERATURE, 
    MHA_SENSOR_TYPE_VALVE, 
    MHA_SENSOR_TYPE_OFFSET,
    MHA_SENSOR_TYPE_ECO_BUTTON,
    ]

# map sensor type to unit
MHA_UNIT_HA_CAST = {
    MHA_SENSOR_TYPE_TEMPERATURE: TEMP_CELSIUS,
    MHA_SENSOR_TYPE_SET_TEMPERATURE: TEMP_CELSIUS,
    MHA_SENSOR_TYPE_VALVE: '%',
    MHA_SENSOR_TYPE_OFFSET: TEMP_CELSIUS,
    MHA_SENSOR_TYPE_ECO_BUTTON: '',
    MHA_SENSOR_TYPE_DUTY: '%',
}

# map sensor type to icon
MHA_ICON_HA_CAST = {
    MHA_SENSOR_TYPE_TEMPERATURE: 'mdi:thermometer',
    MHA_SENSOR_TYPE_SET_TEMPERATURE: 'mdi:thermometer',
    MHA_SENSOR_TYPE_VALVE: 'mdi:radiator',
    MHA_SENSOR_TYPE_OFFSET: 'mdi:delta',
    MHA_SENSOR_TYPE_ECO_BUTTON: 'mdi:home-automation',
    MHA_SENSOR_TYPE_DUTY: 'mdi:radio-tower',
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Iterate through all MAX! Devices and add sensors from termostats."""
    if discovery_info is None:
        return

    devices = []
    for cube_hex_address, handler in hass.data[DATA_KEY].items():
        handler.update()
        # duty sensor
        devices.append(
            MaxHomeAutomationDutySensor (handler, "Cube {} - Duty".format(cube_hex_address)))
        # walk through devices
        for device in handler._cube_json[MHA_API_DEVICES]:

            #we have thermostat
            if device.get(MHA_API_TYPE, '') == MHA_API_RADIATOR_THERMOSTAT:
                device_address = device.get(MHA_API_ADDRESS, None)
                device_name = device.get(MHA_API_NAME, None)
                if device_address is not None and device_name is not None:
                    devices.append(
                        MaxHomeAutomationSensor (handler, device_name + " - Temperature", device_address, MHA_SENSOR_TYPE_TEMPERATURE))
                    devices.append(
                        MaxHomeAutomationSensor (handler, device_name + " - Target Temperature", device_address, MHA_SENSOR_TYPE_SET_TEMPERATURE))
                    devices.append(
                        MaxHomeAutomationSensor (handler, device_name + " - Valve", device_address, MHA_SENSOR_TYPE_VALVE))
                    devices.append(
                        MaxHomeAutomationSensor (handler, device_name + " - Offset", device_address, MHA_SENSOR_TYPE_OFFSET))
                                
            if device.get(MHA_API_TYPE, '') == MHA_API_ECO_BUTTON:
                device_address = device.get(MHA_API_ADDRESS, None)
                device_name = device.get(MHA_API_NAME, None)
                if device_address is not None and device_name is not None:
                    devices.append(
                        MaxHomeAutomationSensor (handler, device_name + " - Mode", device_address, MHA_SENSOR_TYPE_ECO_BUTTON))
                                
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
        # read current value
        self.update()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def sensor_type (self):
        return self._sensor_type;

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return MHA_UNIT_HA_CAST.get(self.sensor_type, None)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return MHA_ICON_HA_CAST.get(self.sensor_type, None)
    
    def update(self):
        """Get latest data from MAX! Home Automation"""
        self._cubehandle.update()
        # find the device
        device = self._cubehandle.device_by_address(self._device_address)
        # device not found
        if device is None:
            self._state = None
            return False
        # update internal values
        value = device.get(self.sensor_type, None)
        self._state = (
            value
                if self.sensor_type != MHA_SENSOR_TYPE_ECO_BUTTON 
            else 
                # translate operation mode of ECO button
                MAP_MHA_OPERATION_MODE_HASS.get(value, None)
            )
        
class MaxHomeAutomationDutySensor(Entity):
    """Representation of a Max! Home Automation Cube duty sensor."""
    
    def __init__(self, cubehandle, name):
        """Initialize the sensor."""
        # store values
        self._cubehandle = cubehandle
        self._name = name
        self._state = None
        # read current value
        self.update()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name
    
    @property
    def sensor_type (self):
        return MHA_SENSOR_TYPE_DUTY;

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return MHA_UNIT_HA_CAST.get(self.sensor_type, None)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return MHA_ICON_HA_CAST.get(self.sensor_type, None)
    
    def update(self):
        """Get latest data from MAX! Home Automation"""
        self._cubehandle.update()
        # update internal values
        self._state = self._cubehandle._cube_duty