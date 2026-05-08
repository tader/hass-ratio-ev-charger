"""Binary sensors for Ratio EV Charger."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import RatioCharger
from .const import DOMAIN
from .coordinator import RatioDataUpdateCoordinator
from .entity import RatioEntity


@dataclass(frozen=True, kw_only=True)
class RatioBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe Ratio binary sensor."""

    value_fn: Callable[[RatioCharger], bool | None]


DESCRIPTIONS = (
    RatioBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        value_fn=lambda charger: charger.charging,
    ),
    RatioBinarySensorEntityDescription(
        key="car_connected",
        translation_key="car_connected",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda charger: charger.car_connected,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ratio binary sensors."""

    coordinator: RatioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RatioBinarySensor(coordinator, charger, description)
        for charger in coordinator.data
        for description in DESCRIPTIONS
    )


class RatioBinarySensor(RatioEntity, BinarySensorEntity):
    """Ratio binary sensor."""

    entity_description: RatioBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: RatioDataUpdateCoordinator,
        charger: RatioCharger,
        description: RatioBinarySensorEntityDescription,
    ) -> None:
        """Initialize sensor."""

        super().__init__(coordinator, charger)
        self.entity_description = description
        self._attr_unique_id = f"{charger.serial_number}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return binary sensor state."""

        charger = self.charger
        if charger is None:
            return None
        return self.entity_description.value_fn(charger)
