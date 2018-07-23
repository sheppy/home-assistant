"""
Support for Dyson Pure Cool Link Sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.dyson/
"""
import asyncio
import logging

from homeassistant.components.dyson import DYSON_DEVICES
from homeassistant.const import STATE_OFF, TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

DEPENDENCIES = ['dyson']

SENSOR_UNITS = {
    'air_quality': 'level',
    'dust': 'level',
    'filter_life': 'hours',
    'humidity': '%',
}

SENSOR_UNITS_V2 = {
    'temperature': 'C°',
    'particulate_matter': 'μg/m3',
    'volatile_organinc_compounds': 'level',
    'nitrogen_dioxide': 'level',
    'filter_state': '%',

}

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Dyson Sensors."""
    _LOGGER.debug("Creating new Dyson fans")
    devices = []
    unit = hass.config.units.temperature_unit
    # Get Dyson Devices from parent component
    from ..lib.libpurecoollink.dyson_pure_cool_link import DysonPureCoolLink
    from ..lib.libpurecoollink.dyson_pure_cool import DysonPureCool
    for device in hass.data[DYSON_DEVICES]:
        if isinstance(device, DysonPureCool):
            devices.append(DysonTemperatureSensor(hass, device, unit))
            devices.append(DysonHumiditySensor(hass, device))
            devices.append(DysonParticulateMatter25Sensor(hass, device))
            devices.append(DysonParticulateMatter10Sensor(hass, device))
            devices.append(DysonVolatileOrganicCompoundsSensor(hass, device))
            devices.append(DysonNitrogenDioxideSensor(hass, device))
            devices.append(DysonCarbonFilterStateSensor(hass, device))
            devices.append(DysonHepaFilterStateSensor(hass, device))
        elif isinstance(device, DysonPureCoolLink):
            devices.append(DysonFilterLifeSensor(hass, device))
            devices.append(DysonDustSensor(hass, device))
            devices.append(DysonHumiditySensor(hass, device))
            devices.append(DysonTemperatureSensor(hass, device, unit))
            devices.append(DysonAirQualitySensor(hass, device))
    add_devices(devices)


class DysonSensor(Entity):
    """Representation of Dyson sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson filter life sensor."""
        self.hass = hass
        self._device = device
        self._old_value = None
        self._name = None

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self.hass.async_add_job(
            self._device.add_message_listener, self.on_message)

    def on_message(self, message):
        """Handle new messages which are received from the fan."""
        # Prevent refreshing if not needed
        if self._old_value is None or self._old_value != self.state:
            _LOGGER.debug("Message received for %s device: %s", self.name,
                          message)
            self._old_value = self.state
            self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the dyson sensor name."""
        return self._name


class DysonFilterLifeSensor(DysonSensor):
    """Representation of Dyson filter life sensor (in hours)."""

    def __init__(self, hass, device):
        """Create a new Dyson filter life sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} filter life".format(self._device.name)

    @property
    def state(self):
        """Return filter life in hours."""
        if self._device.state:
            return int(self._device.state.filter_life)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS['filter_life']


class DysonDustSensor(DysonSensor):
    """Representation of Dyson Dust sensor (lower is better)."""

    def __init__(self, hass, device):
        """Create a new Dyson Dust sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} dust".format(self._device.name)

    @property
    def state(self):
        """Return Dust value."""
        if self._device.environmental_state:
            return self._device.environmental_state.dust
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS['dust']


class DysonHumiditySensor(DysonSensor):
    """Representation of Dyson Humidity sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson Humidity sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} humidity".format(self._device.name)

    @property
    def state(self):
        """Return Dust value."""
        if self._device.environmental_state:
            if self._device.environmental_state.humidity == 0:
                return STATE_OFF
            return self._device.environmental_state.humidity
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS['humidity']


class DysonTemperatureSensor(DysonSensor):
    """Representation of Dyson Temperature sensor."""

    def __init__(self, hass, device, unit):
        """Create a new Dyson Temperature sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} temperature".format(self._device.name)
        self._unit = unit

    @property
    def state(self):
        """Return Dust value."""
        if self._device.environmental_state:
            temperature_kelvin = self._device.environmental_state.temperature
            if temperature_kelvin == 0:
                return STATE_OFF
            if self._unit == TEMP_CELSIUS:
                return float("{0:.1f}".format(temperature_kelvin - 273.15))
            return float("{0:.1f}".format(temperature_kelvin * 9 / 5 - 459.67))
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit


class DysonAirQualitySensor(DysonSensor):
    """Representation of Dyson Air Quality sensor (lower is better)."""

    def __init__(self, hass, device):
        """Create a new Dyson Air Quality sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} air quality".format(self._device.name)

    @property
    def state(self):
        """Return Air Quality value."""
        if self._device.environmental_state:
            return self._device.environmental_state.volatil_organic_compounds
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS['air_quality']


class DysonParticulateMatter25Sensor(DysonSensor):
    """Representation of Dyson pm25 sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson pm25 sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} particulate matter 2.5 μg/m3".format(self._device.name)

    @property
    def state(self):
        """Return pm25 level."""
        if self._device.state:
            return int(self._device.environmental_state.particulate_matter_25)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['particulate_matter']


class DysonParticulateMatter10Sensor(DysonSensor):
    """Representation of Dyson pm10 sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson pm10 sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} particulate matter 10 μg/m3".format(self._device.name)

    @property
    def state(self):
        """Return pm10 level."""
        if self._device.state:
            return int(self._device.environmental_state.particulate_matter_10)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['particulate_matter']


class DysonNitrogenDioxideSensor(DysonSensor):
    """Representation of Dyson no2 sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson no2 sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} nitrogen dioxide".format(self._device.name)

    @property
    def state(self):
        """Return no2 level."""
        if self._device.state:
            return int(self._device.environmental_state.nitrogen_dioxide)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['nitrogen_dioxide']


class DysonVolatileOrganicCompoundsSensor(DysonSensor):
    """Representation of Dyson VOC sensor."""

    def __init__(self, hass, device):
        """Create a new Dyson voc sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} volatile orgainc compounds".format(self._device.name)

    @property
    def state(self):
        """Return voc level."""
        if self._device.state:
            return int(self._device.environmental_state.volatile_organic_compounds)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['volatile_organinc_compounds']


class DysonCarbonFilterStateSensor(DysonSensor):
    """Representation of Dyson carbon filter state sensor (in %)."""

    def __init__(self, hass, device):
        """Create a new Dyson carbon filter state sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} carbon filter state".format(self._device.name)

    @property
    def state(self):
        """Return carbon filter state in %."""
        if self._device.state:
            return int(self._device.state.carbon_filter_state)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['filter_state']


class DysonHepaFilterStateSensor(DysonSensor):
    """Representation of Dyson carbon filter state sensor (in %)."""

    def __init__(self, hass, device):
        """Create a new Dyson carbon filter state sensor."""
        DysonSensor.__init__(self, hass, device)
        self._name = "{} hepa filter state".format(self._device.name)

    @property
    def state(self):
        """Return hepa filter state in %."""
        if self._device.state:
            return int(self._device.state.hepa_filter_state)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS_V2['filter_state']
