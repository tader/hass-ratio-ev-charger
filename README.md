# Ratio EV Charger for Home Assistant

Custom Home Assistant integration for Ratio EV Chargers using the Ratio cloud API.

## Entities

Required:

- `binary_sensor.<charger>_car_connected`
- `binary_sensor.<charger>_charging`
- `sensor.<charger>_charging_power` in kW

## Install with HACS

1. Add this repository as a custom repository in HACS.
2. Category: Integration.
3. Install `Ratio EV Charger`.
4. Restart Home Assistant.
5. Add integration: Settings -> Devices & services -> Add integration -> Ratio EV Charger.

## Configuration

The config flow asks for your Ratio account username and password once. Home Assistant stores them in the config entry and also stores the Cognito refresh token returned by Ratio. Runtime polling renews access tokens with that refresh token. If the refresh token is revoked or expires, the integration falls back to the stored credentials and updates the stored refresh token again.

Advanced API settings are pre-filled from the known Ratio cloud values:

- API base URL: `https://8q4y72fwo3.execute-api.eu-west-1.amazonaws.com/prod`
- Cognito user pool ID: `eu-west-1_mH4sFjLoF`
- Cognito client ID: `78cs05mc0hc5ibqv1tui22n962`
- AWS region: `eu-west-1`

Polling interval is 30 seconds while a charger is charging, otherwise 60 seconds.

## Notes

`actualChargingPower` is converted from watts to kW.

Energy totals are intentionally not calculated by this integration. Home Assistant can calculate energy from `sensor.<charger>_charging_power` with helpers such as Integration and Utility Meter.
