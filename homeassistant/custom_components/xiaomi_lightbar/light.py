import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.scaling import scale_to_ranged_value

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)

from xiaomi_lightbar import Lightbar

from .const import (
    DOMAIN, DEVICE_ID, CE_PIN, CS_PIN,
    BRIGHTNESS_SCALE, COLOR_TEMP_SCALE, KELVIN_SCALE
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""

    data = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Setting up lights %s", data)

    entities = [LightbarEntity(data[CE_PIN], data[CS_PIN], data[DEVICE_ID])]
    async_add_entities(entities)


class LightbarEntity(LightEntity):

    def __init__(self, ce_pin: int, cs_pin: int, device_id: int):
        """Initialize the state variable"""

        self._attr_is_on = False
        self._attr_supported_color_modes = [ColorMode.COLOR_TEMP]
        self._attr_min_color_temp_kelvin = KELVIN_SCALE[0]
        self._attr_max_color_temp_kelvin = KELVIN_SCALE[1]

        if ce_pin >= 0:
            try:
                self._device = Lightbar(ce_pin, cs_pin, device_id)
            except RuntimeError:
                raise CannotConnect
        else:  # Just for debugging
            self._device = DummyLightbar(ce_pin, cs_pin, device_id)

        _LOGGER.debug("LightbarEntity constructor (%s %s %s)",
                      ce_pin, cs_pin, device_id)

    @property
    def unique_id(self):
        return f"{self._device.id:0{6}x}"

    def turn_on(self, **kwargs):
        _LOGGER.debug("Turning on %s", kwargs)
        if not self.is_on:
            self._device.on_off()
            self._attr_is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            self._attr_brightness = brightness
            val = scale_to_ranged_value((0, 255), BRIGHTNESS_SCALE, brightness)
            self._device.brightness(int(val))
            _LOGGER.debug("Brightness %s", val)

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            self._attr_color_temp_kelvin = kelvin
            val = scale_to_ranged_value(KELVIN_SCALE, COLOR_TEMP_SCALE, kelvin)
            self._device.color_temp(int(val))
            _LOGGER.debug("Kelvin %s", val)

    def turn_off(self, **kwargs):
        _LOGGER.debug("Turning off %s", kwargs)
        if self.is_on:
            self._attr_is_on = False
            self._device.on_off()


class CannotConnect(HomeAssistantError):
    """Error to indicate device is not responding."""


class DummyLightbar(Lightbar):
    """A Lightbar that does nothing"""
    
    def __init__(self, ce_pin, cs_pin, device_id):
        self.counter = 0
        self.repetitions = 0
        self.id = device_id
