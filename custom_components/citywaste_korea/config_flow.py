"""Config flow for CityWaste Korea."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv

from .citywaste_api import CityWasteApiError, CityWasteClient
from .const import (
    CONF_APTDONG,
    CONF_APTHONO,
    CONF_MONITORED_CONDITIONS,
    CONF_TAGPRINTCD,
    DEFAULT_MONITORED_CONDITIONS,
    DEFAULT_NAME,
    DOMAIN,
    MONITORED_CONDITIONS,
)

_LOGGER = logging.getLogger(__name__)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
            vol.Required(
                CONF_TAGPRINTCD, default=defaults.get(CONF_TAGPRINTCD, "")
            ): str,
            vol.Required(CONF_APTDONG, default=defaults.get(CONF_APTDONG, 101)): cv.positive_int,
            vol.Required(CONF_APTHONO, default=defaults.get(CONF_APTHONO, 1004)): cv.positive_int,
            vol.Optional(
                CONF_MONITORED_CONDITIONS,
                default=defaults.get(
                    CONF_MONITORED_CONDITIONS, DEFAULT_MONITORED_CONDITIONS
                ),
            ): cv.multi_select({key: value[0] for key, value in MONITORED_CONDITIONS.items()}),
        }
    )


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by checking the CityWaste endpoint."""
    client = CityWasteClient(
        data[CONF_TAGPRINTCD], int(data[CONF_APTDONG]), int(data[CONF_APTHONO])
    )
    result = await hass.async_add_executor_job(client.fetch_month_data)
    return result


class CityWasteKoreaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CityWaste Korea."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_TAGPRINTCD] = user_input[CONF_TAGPRINTCD].strip()
            unique_id = (
                f"{user_input[CONF_TAGPRINTCD]}_"
                f"{user_input[CONF_APTDONG]}_"
                f"{user_input[CONF_APTHONO]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await _validate_input(self.hass, user_input)
            except CityWasteApiError as err:
                _LOGGER.warning("CityWaste validation failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected CityWaste validation error: %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create the options flow."""
        return CityWasteKoreaOptionsFlow(config_entry)


class CityWasteKoreaOptionsFlow(config_entries.OptionsFlow):
    """Handle CityWaste Korea options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}
        current = dict(self.config_entry.data)
        current.update(dict(self.config_entry.options))

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input)
            except CityWasteApiError as err:
                _LOGGER.warning("CityWaste options validation failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected CityWaste options error: %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(current),
            errors=errors,
        )
