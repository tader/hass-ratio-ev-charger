"""Tests for Ratio API payload normalization."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeCognito:
    """Import stub for pycognito."""


sys.modules.setdefault("pycognito", types.SimpleNamespace(Cognito=FakeCognito))
sys.modules.setdefault("requests", types.SimpleNamespace(request=lambda *args, **kwargs: None))

API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ratio_ev_charger"
    / "api.py"
)
SPEC = importlib.util.spec_from_file_location("ratio_ev_charger_api", API_PATH)
api = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)


def _charger_payload(charging_state: str, actual_power: int) -> dict:
    return {
        "name": None,
        "serialNumber": "PTEST000000001",
        "cloudConnectionState": "Online",
        "chargerStatus": {
            "isChargeStartAllowed": False,
            "isChargeStopAllowed": True,
            "indicators": {
                "chargingState": charging_state,
                "isChargeSessionActive": True,
                "isChargingPaused": False,
                "isChargingDisabled": False,
                "isVehicleConnected": True,
                "isPowerReducedByDSO": False,
                "errors": [],
            },
        },
        "chargeSessionStatus": {
            "actualChargingPower": actual_power,
        },
    }


class ApiNormalizationTest(unittest.TestCase):
    """Captured status payload normalization."""

    def test_vehicle_detected_is_connected_but_not_charging(self) -> None:
        charger = api._normalize_charger(_charger_payload("VehicleDetected", 0))

        self.assertIs(charger.car_connected, True)
        self.assertIs(charger.charging, False)
        self.assertEqual(charger.charging_power_kw, 0)

    def test_charging_state_controls_charging_boolean_and_power_kw(self) -> None:
        charger = api._normalize_charger(_charger_payload("Charging", 1091))

        self.assertIs(charger.car_connected, True)
        self.assertIs(charger.charging, True)
        self.assertEqual(charger.charging_power_kw, 1.091)

    def test_overview_response_supports_multiple_chargers(self) -> None:
        payload = {
            "chargers": [
                _charger_payload("Charging", 1091),
                {**_charger_payload("VehicleDetected", 0), "serialNumber": "P2"},
            ]
        }

        chargers = [api._normalize_charger(item) for item in payload["chargers"]]

        self.assertEqual(
            [charger.serial_number for charger in chargers],
            ["PTEST000000001", "P2"],
        )
        self.assertEqual([charger.charging for charger in chargers], [True, False])


if __name__ == "__main__":
    unittest.main()
