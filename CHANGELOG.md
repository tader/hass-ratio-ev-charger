# Changelog

## Unreleased

- Add Ratio Electric icon assets for HACS and Home Assistant integration display.

## 0.1.0 - 2026-05-08

- Initial HACS-ready custom integration for Ratio EV Charger.
- Add entities for car connected, charging, and charging power in kW.
- Poll Ratio overview endpoint for all chargers on the account.
- Use Cognito refresh-token auth for unattended Home Assistant operation.
- Poll every 30 seconds while charging and every 60 seconds while idle.
