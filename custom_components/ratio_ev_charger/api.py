"""Ratio EV Charger cloud API client."""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import requests
from pycognito import Cognito

REQUEST_TIMEOUT = 30
TOKEN_MIN_VALIDITY_SECONDS = 300

Executor = Callable[..., Awaitable[Any]]


class RatioApiError(Exception):
    """Raised when the Ratio API returns an error."""


@dataclass(slots=True)
class RatioCharger:
    """Normalized charger status."""

    name: str | None
    serial_number: str
    cloud_connection_state: str | None
    charging: bool
    car_connected: bool
    charging_power_kw: float | None
    raw: dict[str, Any]


@dataclass(slots=True)
class RatioAuthResult:
    """Cognito authentication result."""

    user_id: str
    access_token: str
    id_token: str
    refresh_token: str
    expires_at: float


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT payload without verification."""

    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))


def extract_user_id(id_token: str, access_token: str) -> str:
    """Extract Cognito user id from available tokens."""

    for token in (id_token, access_token):
        try:
            user_id = decode_jwt_payload(token).get("sub")
        except (IndexError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if user_id:
            return str(user_id)
    raise RatioApiError("Could not extract user id from Cognito tokens")


class RatioApiClient:
    """Small synchronous Ratio client wrapped by Home Assistant executor jobs."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        refresh_token: str | None,
        user_id: str,
        user_pool_id: str,
        client_id: str,
        api_base_url: str,
        region: str,
        executor: Executor,
    ) -> None:
        self._username = username
        self._password = password
        self._refresh_token = refresh_token
        self._user_id = user_id
        self._user_pool_id = user_pool_id
        self._client_id = client_id
        self._api_base_url = api_base_url.rstrip("/")
        self._region = region
        self._executor = executor
        self._access_token: str | None = None
        self._id_token: str | None = None
        self._token_expires_at = 0.0

    @classmethod
    async def async_validate_login(
        cls,
        *,
        username: str,
        password: str,
        user_pool_id: str,
        client_id: str,
        region: str,
        executor: Executor,
    ) -> RatioAuthResult:
        """Validate credentials and return reusable Cognito tokens."""

        def authenticate() -> RatioAuthResult:
            try:
                cognito = Cognito(
                    user_pool_id=user_pool_id,
                    client_id=client_id,
                    user_pool_region=region,
                    username=username,
                )
                cognito.authenticate(password=password)
                return RatioAuthResult(
                    user_id=extract_user_id(cognito.id_token, cognito.access_token),
                    access_token=cognito.access_token,
                    id_token=cognito.id_token,
                    refresh_token=cognito.refresh_token,
                    expires_at=_jwt_exp(cognito.access_token) or time.time() + 3600,
                )
            except Exception as err:
                raise RatioApiError(str(err)) from err

        return await executor(authenticate)

    async def async_get_data(self) -> list[RatioCharger]:
        """Fetch current charger data."""

        return await self._executor(self._get_data)

    @property
    def refresh_token(self) -> str | None:
        """Return current refresh token."""

        return self._refresh_token

    def _get_data(self) -> list[RatioCharger]:
        self._ensure_authenticated()
        chargers_payload = self._request_json(
            "GET",
            f"/users/{self._user_id}/chargers/status",
            params={"id": "overview"},
        )
        chargers = chargers_payload.get("chargers", [])
        if not isinstance(chargers, list):
            raise RatioApiError("Invalid chargers response")

        normalized: list[RatioCharger] = []
        for charger in chargers:
            if not isinstance(charger, dict):
                continue
            serial_number = charger.get("serialNumber")
            if not serial_number:
                continue
            normalized.append(_normalize_charger(charger))
        return normalized

    def _ensure_authenticated(self) -> None:
        if (
            self._access_token
            and time.time() < self._token_expires_at - TOKEN_MIN_VALIDITY_SECONDS
        ):
            return

        if self._refresh_token:
            try:
                self._renew_access_token()
                return
            except RatioApiError:
                self._access_token = None
                self._id_token = None
                self._token_expires_at = 0.0

        self._authenticate_with_password()

    def _renew_access_token(self) -> None:
        try:
            cognito = Cognito(
                user_pool_id=self._user_pool_id,
                client_id=self._client_id,
                user_pool_region=self._region,
                username=self._username,
                access_token=self._access_token,
                id_token=self._id_token,
                refresh_token=self._refresh_token,
            )
            cognito.renew_access_token()
            self._access_token = cognito.access_token
            self._id_token = cognito.id_token
            self._refresh_token = cognito.refresh_token
            self._token_expires_at = (
                _jwt_exp(cognito.access_token) or time.time() + 3600
            )
        except Exception as err:
            raise RatioApiError(str(err)) from err

    def _authenticate_with_password(self) -> None:
        try:
            cognito = Cognito(
                user_pool_id=self._user_pool_id,
                client_id=self._client_id,
                user_pool_region=self._region,
                username=self._username,
            )
            cognito.authenticate(password=self._password)
            self._access_token = cognito.access_token
            self._id_token = cognito.id_token
            self._refresh_token = cognito.refresh_token
            self._token_expires_at = (
                _jwt_exp(cognito.access_token) or time.time() + 3600
            )
        except Exception as err:
            raise RatioApiError(str(err)) from err

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not self._access_token:
            raise RatioApiError("Not authenticated")

        url = f"{self._api_base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
        if response.status_code in (401, 403):
            self._access_token = None
            self._ensure_authenticated()
            headers["Authorization"] = f"Bearer {self._access_token}"
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
        if response.status_code != 200:
            raise RatioApiError(
                f"Ratio API error {response.status_code}: {response.text}"
            )
        return response.json()


def _jwt_exp(token: str) -> int | None:
    try:
        exp = decode_jwt_payload(token).get("exp")
    except (IndexError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    try:
        return int(exp)
    except (TypeError, ValueError):
        return None


def _normalize_charger(charger: dict[str, Any]) -> RatioCharger:
    status = (
        charger.get("chargerStatus")
        if isinstance(charger.get("chargerStatus"), dict)
        else {}
    )
    indicators = (
        status.get("indicators")
        if isinstance(status.get("indicators"), dict)
        else {}
    )
    session_status = (
        charger.get("chargeSessionStatus")
        if isinstance(charger.get("chargeSessionStatus"), dict)
        else {}
    )

    return RatioCharger(
        name=charger.get("name"),
        serial_number=str(charger["serialNumber"]),
        cloud_connection_state=_as_optional_str(charger.get("cloudConnectionState")),
        charging=_charger_is_charging(charger),
        car_connected=_as_bool(indicators.get("isVehicleConnected")),
        charging_power_kw=_power_to_kw(session_status.get("actualChargingPower")),
        raw=charger,
    )


def _charger_is_charging(charger: dict[str, Any]) -> bool:
    status = (
        charger.get("chargerStatus")
        if isinstance(charger.get("chargerStatus"), dict)
        else {}
    )
    indicators = (
        status.get("indicators")
        if isinstance(status.get("indicators"), dict)
        else {}
    )
    return indicators.get("chargingState") == "Charging"


def _power_to_kw(value: Any) -> float | None:
    if value is None:
        return None
    try:
        power = float(value)
    except (TypeError, ValueError):
        return None
    return power / 1000.0


def _as_bool(value: Any) -> bool:
    return bool(value)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)

