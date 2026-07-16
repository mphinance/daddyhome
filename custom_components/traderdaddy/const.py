"""Constants for the TraderDaddy Pro integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "traderdaddy"

CONF_API_KEY = "api_key"
CONF_SYMBOL = "symbol"

DEFAULT_SYMBOL = "SPY"

PLATFORMS = ["sensor", "binary_sensor", "event", "calendar"]

# Fast-tier cadence — market-wide vitals + the tracked symbol's core reads.
# E-ink / smart-home reads don't need to be fast, and a slow cadence keeps
# us comfortably under the per-key rate limit.
SCAN_INTERVAL_OPEN = timedelta(minutes=2)
SCAN_INTERVAL_CLOSED = timedelta(minutes=15)

# Slow-tier cadence — screeners, calendars, and the heavier per-symbol
# analytics. These change slowly enough that a much longer interval loses
# nothing (mirrors the SDK's own DEFAULT_TTLS in traderdaddy/cache.py).
SCAN_INTERVAL_SLOW_OPEN = timedelta(minutes=10)
SCAN_INTERVAL_SLOW_CLOSED = timedelta(minutes=30)

# run_screener rotates one key per slow-tier cycle (same trick DaddyBoard's
# daemon uses for its rotating main-stage panel) so all ten screeners get
# surfaced over time without hammering the endpoint.
SCREENER_ROTATION = [
    "daily-cuts",
    "momentum",
    "csp-wheel",
    "volatility-squeeze",
    "bullish-pullback",
    "small-cap",
    "volatility-surge",
    "gamma-scan",
    "leaps",
    "leveraged",
]

# get_ipo_scanner takes a required `view`; rotate through all four.
IPO_VIEW_ROTATION = ["upcoming", "recent", "radar", "transitions"]

# Composite risk score (0-7, see MarketHealth.compositeScore) at/above which
# binary_sensor.td_elevated_risk turns on.
ELEVATED_RISK_THRESHOLD = 3

# Community conviction score (0-100) at/above which binary_sensor.td_high_conviction
# turns on for the tracked symbol.
HIGH_CONVICTION_THRESHOLD = 70
