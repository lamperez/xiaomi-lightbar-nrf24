"""Config flow for Xiaomi Mi Computer Monitor Light Bar integration."""

from typing import Any
import logging
import voluptuous as vol

from xiaomi_lightbar import Lightbar

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (DOMAIN, DEVICE_ID, CE_PIN, CS_PIN)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(DEVICE_ID, default="0x000000"): str,
        vol.Required(CE_PIN, default=25): int,
        vol.Required(CS_PIN, default=0): int,
    }
)


async def validate_input(hass: HomeAssistant,
                         data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input and check device availability"""

    # device_id must be an integer between 0 and 0xFFFFFF (3 bytes)
    try:
        device_id = int(data[DEVICE_ID], 0)
    except ValueError:
        raise InvalidID

    if device_id < 0 or device_id > 0xFFFFFF:
        raise InvalidID

    data[DEVICE_ID] = device_id
    ce_pin = data[CE_PIN]
    cs_pin = data[CS_PIN]

    if ce_pin >= 0:  # ce_pin<0: debugging
        try:
            Lightbar(ce_pin, cs_pin, device_id)
        except RuntimeError:
            raise CannotConnect

    return {"title": f"Light bar 0x{device_id:0{6}x}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi Mi Computer Monitor Light Bar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidID:
                errors["base"] = "invalid_id"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                device_unique_id = user_input[DEVICE_ID]
                await self.async_set_unique_id(device_unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"],
                                               data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class InvalidID(HomeAssistantError):
    """Error to indicate there is invalid device ID (hex number)."""


class CannotConnect(HomeAssistantError):
    """Error to indicate device is not responding."""
