"""Support for MAX! Devices and add binary sensors from thermostats."""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from .__init__ import (
    DATA_KEY, MHA_API_DEVICES, MHA_API_ADDRESS, MHA_API_NAME, 
    MHA_API_RADIATOR_THERMOSTAT, MHA_API_TYPE, 
    MHA_API_ERROR, MHA_API_INITIALIZED, MHA_API_BATTERY,
    MHA_API_PANEL_LOCKED, MHA_API_LINK_ERROR, 
    MHA_API_OPEN,
    MHA_API_SHUTTER_CONTACT, MHA_API_ECO_BUTTON
    )

_LOGGER = logging.getLogger(__name__)

MHA_SENSOR_TYPE_ERROR = MHA_API_ERROR
MHA_SENSOR_TYPE_INITIALIZED = MHA_API_INITIALIZED
MHA_SENSOR_TYPE_BATTERY = MHA_API_BATTERY
MHA_SENSOR_TYPE_PANEL_LOCKED = MHA_API_PANEL_LOCKED
MHA_SENSOR_TYPE_LINK_ERROR = MHA_API_LINK_ERROR
MHA_SENSOR_TYPE_SHUTTER_CONTACT = MHA_API_OPEN

# allowed sensors types
MHA_ALLOWED_SENSOR_TYPES = [
    MHA_SENSOR_TYPE_ERROR, 
    MHA_SENSOR_TYPE_INITIALIZED, 
    MHA_SENSOR_TYPE_BATTERY,
    MHA_SENSOR_TYPE_PANEL_LOCKED, 
    MHA_SENSOR_TYPE_LINK_ERROR,
    MHA_SENSOR_TYPE_SHUTTER_CONTACT,
    ]

MHA_DEVICE_CLASSES_CAST = {
    MHA_SENSOR_TYPE_ERROR: 'problem',
    MHA_SENSOR_TYPE_INITIALIZED: 'plug',
    MHA_SENSOR_TYPE_BATTERY: 'battery',
    MHA_SENSOR_TYPE_PANEL_LOCKED: 'lock',
    MHA_SENSOR_TYPE_LINK_ERROR: 'connectivity',
    MHA_SENSOR_TYPE_SHUTTER_CONTACT: 'window'
}

MHA_VALUE_CAST = {
    MHA_SENSOR_TYPE_ERROR: {True: True, False: False, },
    MHA_SENSOR_TYPE_INITIALIZED: {True: True, False: False, },
    MHA_SENSOR_TYPE_BATTERY: {True: True, False: False, },
    MHA_SENSOR_TYPE_PANEL_LOCKED: {True: False, False: True, },
    MHA_SENSOR_TYPE_LINK_ERROR: {True: False, False: True, },
    MHA_SENSOR_TYPE_SHUTTER_CONTACT: {True: True, False: False, },
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Iterate through all MAX! Devices and add binary sensors from thermostats."""
    if discovery_info is None:
        return

    devices = []
    for handler in hass.data[DATA_KEY].values():
        handler.update()
        # walk through devices
        for device in handler._cube_json[MHA_API_DEVICES]:
            #we have thermostat
            if device.get(MHA_API_TYPE, '') == MHA_API_RADIATOR_THERMOSTAT:
                device_address = device.get(MHA_API_ADDRESS, None)
                device_name = device.get(MHA_API_NAME, None)
                if device_address is not None and device_name is not None:
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Error", device_address, MHA_SENSOR_TYPE_ERROR))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", device_address, MHA_SENSOR_TYPE_INITIALIZED))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", device_address, MHA_SENSOR_TYPE_BATTERY))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Unlocked", device_address, MHA_SENSOR_TYPE_PANEL_LOCKED))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Link", device_address, MHA_SENSOR_TYPE_LINK_ERROR))

            # we have shutter contact
            if device.get(MHA_API_TYPE, '') == MHA_API_SHUTTER_CONTACT:
                device_address = device.get(MHA_API_ADDRESS, None)
                device_name = device.get(MHA_API_NAME, None)
                if device_address is not None and device_name is not None:
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Error", device_address, MHA_SENSOR_TYPE_ERROR))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", device_address, MHA_SENSOR_TYPE_INITIALIZED))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", device_address, MHA_SENSOR_TYPE_BATTERY))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Link", device_address, MHA_SENSOR_TYPE_LINK_ERROR))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Open window", device_address, MHA_SENSOR_TYPE_SHUTTER_CONTACT))
                                
            # we have eco button
            if device.get(MHA_API_TYPE, '') == MHA_API_ECO_BUTTON:
                device_address = device.get(MHA_API_ADDRESS, None)
                device_name = device.get(MHA_API_NAME, None)
                if device_address is not None and device_name is not None:
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Error", device_address, MHA_SENSOR_TYPE_ERROR))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", device_address, MHA_SENSOR_TYPE_INITIALIZED))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", device_address, MHA_SENSOR_TYPE_BATTERY))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Unlocked", device_address, MHA_SENSOR_TYPE_PANEL_LOCKED))
                    devices.append(
                        MaxHomeAutomationBinarySensor (handler, device_name + " - Link", device_address, MHA_SENSOR_TYPE_LINK_ERROR))

    add_entities(devices)


class MaxHomeAutomationBinarySensor(BinarySensorDevice):
    """Representation of a MAX! Cube Binary Sensor device."""

    def __init__(self, handler, name, device_address, sensor_type):
        """Initialize the sensor."""
        # check sensor_type
        if sensor_type not in MHA_ALLOWED_SENSOR_TYPES:
            raise ValueError("Unknown Max! Home Automation sensor type: {}".format(sensor_type))        
        self._cubehandle = handler
        self._name = name
        self._sensor_type = sensor_type
        self._device_address = device_address
        self._read_state = None
        # read current value
        self.update()

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the BinarySensorDevice."""
        return self._name

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return MHA_DEVICE_CLASSES_CAST.get(self.sensor_type, None)
    
    @property
    def sensor_type (self):
        return self._sensor_type;    

    @property
    def is_on(self):
        """Return true if the binary sensor is on/open."""
        if self._read_state is None and self.sensor_type == MHA_SENSOR_TYPE_INITIALIZED:
            return False
        if self._read_state is None:
            return None
        # convert value
        return MHA_VALUE_CAST[self.sensor_type].get(self._read_state, None)

    def update(self):
        """Get latest data from MAX! Cube."""
        self._cubehandle.update()
        device = self._cubehandle.device_by_address(self._device_address)
        # device not found
        if device is None:
            self._read_state = None
            return False
        # update internal state
        self._read_state = device.get(self.sensor_type, None)
