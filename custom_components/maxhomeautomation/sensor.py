"""Support for MAX! Home Automation Thermostats Sensors."""
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.const import TEMP_CELSIUS
from .consts import *
from .__init__ import MaxHomeAutomationDeviceHandler
from .__init__ import MaxHomeAutomationCubeHandler

_LOGGER = logging.getLogger(__name__)

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
                    MaxHomeAutomationSensor (handler, device_name + " - Temperature", MHA_SENSOR_TYPE_TEMPERATURE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Target Temperature", MHA_SENSOR_TYPE_SET_TEMPERATURE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Valve", MHA_SENSOR_TYPE_VALVE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Offset", MHA_SENSOR_TYPE_OFFSET))

                            
            # walk trough wall thermostats
            for wall_thermostat in wall_thermostats:
                device_address = wall_thermostat[CONF_HEX_ADDRESS]
                device_name = wall_thermostat[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Temperature", MHA_SENSOR_TYPE_TEMPERATURE))
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Target Temperature", MHA_SENSOR_TYPE_SET_TEMPERATURE))

                                         
            # walk trough eco buttons
            for eco_button in eco_buttons:
                device_address = eco_button[CONF_HEX_ADDRESS]
                device_name = eco_button[CONF_NAME]
                
                handler = MaxHomeAutomationDeviceHandler(
                    gateway_url_base, cube_address, device_address, scan_interval)
                
                devices.append(
                    MaxHomeAutomationSensor (handler, device_name + " - Mode", MHA_SENSOR_TYPE_ECO_BUTTON))
                
                
            # duty sensor
            handler = MaxHomeAutomationCubeHandler(
                    gateway_url_base, cube_address, scan_interval)
            devices.append(
                MaxHomeAutomationDutySensor (handler, cube_name + " - Duty"))
                
    
    if devices:
        add_entities(devices)

    # platform initialization was successful
    return True

class MaxHomeAutomationSensor(Entity):
    """Representation of a Max! Home Automation sensor."""
    
    def __init__(self, device_handler, name, sensor_type):
        """Initialize the sensor."""
        # check sensor_type
        if sensor_type not in MHA_ALLOWED_SENSOR_TYPES:
            raise ValueError("Unknown Max! Home Automation sensor type: {}".format(sensor_type))
        # store values
        self._device_handler = device_handler
        self._name = name
        self._sensor_type = sensor_type
        self._state = None
        # read current value
        self.update()

    @property
    def should_poll(self):
        """Return the polling state."""
        return True
    
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
        self._device_handler.update()
        # find the device
        device = self._device_handler.data
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
    def should_poll(self):
        """Return the polling state."""
        return True
    
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
        value = self._cubehandle.cube_duty
        # no value 
        if value is None:
            self._state = None
            return False
        # remove '%'
        value = value.replace('%', '')
        # update internal values
        self._state = value