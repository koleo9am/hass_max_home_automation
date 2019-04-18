"""Support for MAX! Devices and add binary sensors from thermostats."""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from .consts import *
from .__init__ import MaxHomeAutomationDeviceHandler

from .consts import VERSION

_LOGGER = logging.getLogger(__name__)

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
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Error", MHA_SENSOR_TYPE_ERROR))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", MHA_SENSOR_TYPE_INITIALIZED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", MHA_SENSOR_TYPE_BATTERY))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Unlocked", MHA_SENSOR_TYPE_PANEL_LOCKED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Link", MHA_SENSOR_TYPE_LINK_ERROR))

                            
            # walk trough wall thermostats
            for wall_thermostat in wall_thermostats:
                device_address = wall_thermostat[CONF_HEX_ADDRESS]
                device_name = wall_thermostat[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Error", MHA_SENSOR_TYPE_ERROR))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", MHA_SENSOR_TYPE_INITIALIZED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", MHA_SENSOR_TYPE_BATTERY))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Unlocked", MHA_SENSOR_TYPE_PANEL_LOCKED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Link", MHA_SENSOR_TYPE_LINK_ERROR))

                
            # walk trough window shutters
            for window_shutter in window_shutters:
                device_address = window_shutter[CONF_HEX_ADDRESS]
                device_name = window_shutter[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Error", MHA_SENSOR_TYPE_ERROR))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", MHA_SENSOR_TYPE_INITIALIZED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", MHA_SENSOR_TYPE_BATTERY))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Link", MHA_SENSOR_TYPE_LINK_ERROR))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Open window", MHA_SENSOR_TYPE_SHUTTER_CONTACT))
                
                
            # walk trough eco buttons
            for eco_button in eco_buttons:
                device_address = eco_button[CONF_HEX_ADDRESS]
                device_name = eco_button[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Error", MHA_SENSOR_TYPE_ERROR))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Initialized", MHA_SENSOR_TYPE_INITIALIZED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Low battery", MHA_SENSOR_TYPE_BATTERY))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Unlocked", MHA_SENSOR_TYPE_PANEL_LOCKED))
                devices.append(
                    MaxHomeAutomationBinarySensor (handler, device_name + " - Link", MHA_SENSOR_TYPE_LINK_ERROR))
               
    
    if devices:
        add_entities(devices)

    # platform initialization was successful
    return True

class MaxHomeAutomationBinarySensor(BinarySensorDevice):
    """Representation of a MAX! Cube Binary Sensor device."""

    def __init__(self, device_handler, name, sensor_type):
        """Initialize the sensor."""
        # check sensor_type
        if sensor_type not in MHA_ALLOWED_SENSOR_TYPES:
            raise ValueError("Unknown Max! Home Automation sensor type: {}".format(sensor_type))        
        self._device_handler = device_handler
        self._name = name
        self._sensor_type = sensor_type
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
        return self._sensor_type 

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
        self._device_handler.update()
        device = self._device_handler.data
        # device not found
        if device is None:
            self._read_state = None
            return False
        # update internal state
        self._read_state = device.get(self.sensor_type, None)
