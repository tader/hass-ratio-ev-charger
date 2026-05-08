"""Sensors for Ratio EV Charger."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import RatioCharger
from .const import DOMAIN
from .coordinator import RatioDataUpdateCoordinator
from .entity import RatioEntity


@dataclass(frozen=True, kw_only=True)
class RatioSensorEntityDescription(SensorEntityDescription):
    """Describe Ratio sensor."""

    value_fn: Callable[[RatioCharger], float | None]


DESCRIPTIONS = (
    RatioSensorEntityDescription(
        key="charging_power",
        translation_key="charging_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda charger: charger.charging_power_kw,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ratio sensors."""

    coordinator: RatioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RatioSensor(coordinator, charger, description)
        for charger in coordinator.data
        for description in DESCRIPTIONS
    )


class RatioSensor(RatioEntity, SensorEntity):
    """Ratio sensor."""

    entity_description: RatioSensorEntityDescription

    def __init__(
        self,
        coordinator: RatioDataUpdateCoordinator,
        charger: RatioCharger,
        description: RatioSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""

        super().__init__(coordinator, charger)
        self.entity_description = description
        self._attr_unique_id = f"{charger.serial_number}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""

        charger = self.charger
        if charger is None:
            return None
        return self.entity_description.value_fn(charger)
