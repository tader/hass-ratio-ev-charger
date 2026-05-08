"""Base entities for Ratio EV Charger."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RatioCharger
from .const import DOMAIN
from .coordinator import RatioDataUpdateCoordinator


class RatioEntity(CoordinatorEntity[RatioDataUpdateCoordinator]):
    """Base Ratio entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RatioDataUpdateCoordinator, charger: RatioCharger) -> None:
        """Initialize entity."""

        super().__init__(coordinator)
        self._serial_number = charger.serial_number
        self._charger_name = charger.name or charger.serial_number
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, charger.serial_number)},
            manufacturer="Ratio Electric",
            name=self._charger_name,
            serial_number=charger.serial_number,
        )

    @property
    def charger(self) -> RatioCharger | None:
        """Return latest charger data."""

        for charger in self.coordinator.data or []:
            if charger.serial_number == self._serial_number:
                return charger
        return None
