"""Constants for the Ratio EV Charger integration."""

from __future__ import annotations

DOMAIN = "ratio_ev_charger"

DEFAULT_API_BASE_URL = "https://8q4y72fwo3.execute-api.eu-west-1.amazonaws.com/prod"
DEFAULT_CLIENT_ID = "78cs05mc0hc5ibqv1tui22n962"
DEFAULT_REGION = "eu-west-1"
DEFAULT_USER_POOL_ID = "eu-west-1_mH4sFjLoF"
CHARGING_SCAN_INTERVAL = 30
IDLE_SCAN_INTERVAL = 60

CONF_API_BASE_URL = "api_base_url"
CONF_CLIENT_ID = "client_id"
CONF_REGION = "region"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_USER_ID = "user_id"
CONF_USER_POOL_ID = "user_pool_id"

PLATFORMS = ["binary_sensor", "sensor"]
