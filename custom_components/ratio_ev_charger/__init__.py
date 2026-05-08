"""Ratio EV Charger integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api import RatioApiClient
from .const import (
    CONF_API_BASE_URL,
    CONF_CLIENT_ID,
    CONF_REGION,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    CONF_USER_POOL_ID,
    DEFAULT_API_BASE_URL,
    DEFAULT_CLIENT_ID,
    DEFAULT_REGION,
    DEFAULT_USER_POOL_ID,
    DOMAIN,
)
from .coordinator import RatioDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ratio EV Charger from a config entry."""

    data = entry.data
    client = RatioApiClient(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        refresh_token=data.get(CONF_REFRESH_TOKEN),
        user_id=data[CONF_USER_ID],
        user_pool_id=data.get(CONF_USER_POOL_ID, DEFAULT_USER_POOL_ID),
        client_id=data.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID),
        api_base_url=data.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL),
        region=data.get(CONF_REGION, DEFAULT_REGION),
        executor=hass.async_add_executor_job,
    )
    coordinator = RatioDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
