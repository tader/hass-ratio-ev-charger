"""Config flow for Ratio EV Charger."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import RatioApiClient, RatioApiError
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


class RatioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Ratio EV Charger config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle initial user step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                auth = await RatioApiClient.async_validate_login(
                    username=str(user_input[CONF_USERNAME]),
                    password=str(user_input[CONF_PASSWORD]),
                    user_pool_id=user_input[CONF_USER_POOL_ID],
                    client_id=user_input[CONF_CLIENT_ID],
                    region=user_input[CONF_REGION],
                    executor=self.hass.async_add_executor_job,
                )
            except RatioApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(auth.user_id)
                self._abort_if_unique_id_configured()
                data = dict(user_input)
                data[CONF_USER_ID] = auth.user_id
                data[CONF_REFRESH_TOKEN] = auth.refresh_token
                return self.async_create_entry(
                    title=str(user_input[CONF_USERNAME]),
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )


def _schema(user_input: dict[str, Any] | None) -> vol.Schema:
    data = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=data.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=data.get(CONF_PASSWORD, "")): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Optional(
                CONF_API_BASE_URL,
                default=data.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL),
            ): str,
            vol.Optional(
                CONF_USER_POOL_ID,
                default=data.get(CONF_USER_POOL_ID, DEFAULT_USER_POOL_ID),
            ): str,
            vol.Optional(
                CONF_CLIENT_ID,
                default=data.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID),
            ): str,
            vol.Optional(CONF_REGION, default=data.get(CONF_REGION, DEFAULT_REGION)): str,
        }
    )
