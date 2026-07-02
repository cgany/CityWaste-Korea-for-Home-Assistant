"""Support for getting statistical data from CityWaste Korea."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .citywaste_api import CityWasteApiError, CityWasteClient
from .const import (
    CONF_APTDONG,
    CONF_APTHONO,
    CONF_MONITORED_CONDITIONS,
    CONF_TAGPRINTCD,
    DEFAULT_MONITORED_CONDITIONS,
    DOMAIN,
    MONITORED_CONDITIONS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CityWaste Korea sensors from a config entry."""
    data = dict(entry.data)
    data.update(dict(entry.options))

    client = CityWasteClient(
        data[CONF_TAGPRINTCD], int(data[CONF_APTDONG]), int(data[CONF_APTHONO])
    )

    async def async_update_data() -> dict[str, Any]:
        try:
            return await hass.async_add_executor_job(client.fetch_month_data)
        except CityWasteApiError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    conditions = data.get(CONF_MONITORED_CONDITIONS) or DEFAULT_MONITORED_CONDITIONS
    async_add_entities(
        CityWasteSensor(coordinator, entry, condition) for condition in conditions
    )


class CityWasteSensor(CoordinatorEntity, SensorEntity):
    """Representation of a CityWaste Korea sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, Any]],
        entry: ConfigEntry,
        condition: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._condition = condition
        variable_info = MONITORED_CONDITIONS[condition]
        self._condition_name = variable_info[0]
        self._attr_name = self._condition_name
        self._attr_icon = variable_info[2]
        self._attr_unique_id = f"{entry.entry_id}_{condition}"

        if condition in ("last_kg", "total_kg"):
            self._attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
            self._attr_device_class = SensorDeviceClass.WEIGHT
            if condition == "total_kg":
                self._attr_state_class = SensorStateClass.TOTAL
        elif condition == "total_count":
            self._attr_state_class = SensorStateClass.TOTAL

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="CityWaste Korea",
            configuration_url="https://www.citywaste.or.kr/portal/status/selectSimpleEmissionQuantity.do",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._condition)
        if isinstance(value, float):
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self._condition != "total_count":
            return None

        data = self.coordinator.data
        last_kg = data.get("last_kg")
        total_kg = data.get("total_kg")

        return {
            "address": data.get("address"),
            "total_count": data.get("total_count"),
            "last_kg": round(last_kg, 2) if isinstance(last_kg, float) else last_kg,
            "last_date": data.get("last_date"),
            "total_kg": round(total_kg, 2) if isinstance(total_kg, float) else total_kg,
        }
