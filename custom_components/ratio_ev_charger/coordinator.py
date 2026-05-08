"""Data coordinator for Ratio EV Charger."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RatioApiClient, RatioApiError, RatioCharger
from .const import (
    CHARGING_SCAN_INTERVAL,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    IDLE_SCAN_INTERVAL,
)

LOGGER = logging.getLogger(__name__)


class RatioDataUpdateCoordinator(DataUpdateCoordinator[list[RatioCharger]]):
    """Fetch Ratio charger data on a shared interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: RatioApiClient,
    ) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=IDLE_SCAN_INTERVAL),
        )
        self.client = client
        self.config_entry = config_entry

    async def _async_update_data(self) -> list[RatioCharger]:
        """Update data from Ratio cloud."""

        try:
            data = await self.client.async_get_data()
        except RatioApiError as err:
            raise UpdateFailed(str(err)) from err

        self.update_interval = timedelta(
            seconds=CHARGING_SCAN_INTERVAL
            if any(charger.charging for charger in data)
            else IDLE_SCAN_INTERVAL
        )

        refresh_token = self.client.refresh_token
        if (
            refresh_token
            and refresh_token != self.config_entry.data.get(CONF_REFRESH_TOKEN)
        ):
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_REFRESH_TOKEN: refresh_token},
            )
        return data
