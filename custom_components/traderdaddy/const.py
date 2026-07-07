"""Constants for the TraderDaddy Pro integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "traderdaddy"

CONF_API_KEY = "api_key"
CONF_SYMBOL = "symbol"

DEFAULT_SYMBOL = "SPY"

PLATFORMS = ["sensor", "binary_sensor"]

# Market-hours cadence — e-ink / smart-home reads don't need to be fast, and a
# slow cadence keeps us comfortably under the per-key rate limit.
SCAN_INTERVAL_OPEN = timedelta(minutes=2)
SCAN_INTERVAL_CLOSED = timedelta(minutes=15)
