"""Slow-tier DataUpdateCoordinator for TraderDaddy Pro.

Owns everything scoped to the tracked symbol plus the heavier/rotating
market-wide tools (screeners, calendars, IPO scanner) — all of it changes
slowly enough that a long interval loses nothing. Shares the same
``TraderDaddy`` client instance as the fast-tier coordinator
(``coordinator.py``); the client is instantiated exactly once, in
``__init__.py``.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from traderdaddy import TraderDaddy, TraderDaddyError, is_market_open

from .const import (
    CONF_SYMBOL,
    DEFAULT_SYMBOL,
    DOMAIN,
    IPO_VIEW_ROTATION,
    SCAN_INTERVAL_SLOW_CLOSED,
    SCAN_INTERVAL_SLOW_OPEN,
    SCREENER_ROTATION,
)

_LOGGER = logging.getLogger(__name__)


class TraderDaddySlowCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the slow-tier TraderDaddy Pro tool set on a long cadence."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TraderDaddy) -> None:
        self.entry = entry
        self.client = client
        self.symbol = (
            entry.options.get(CONF_SYMBOL)
            or entry.data.get(CONF_SYMBOL)
            or DEFAULT_SYMBOL
        )
        self._cycle = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_slow",
            update_interval=SCAN_INTERVAL_SLOW_OPEN,
        )

    @property
    def is_demo(self) -> bool:
        return self.client.mock

    async def _async_update_data(self) -> dict:
        screener_key = SCREENER_ROTATION[self._cycle % len(SCREENER_ROTATION)]
        ipo_view = IPO_VIEW_ROTATION[self._cycle % len(IPO_VIEW_ROTATION)]
        self._cycle += 1

        try:
            data = {
                "run_screener": await self.client.run_screener(screener_key),
                "strategy_ideas": await self.client.strategy_ideas(self.symbol),
                "edge_xray": await self.client.edge_xray(self.symbol),
                "gex_ticker": await self.client.gex_ticker(self.symbol),
                "apex_levels": await self.client.apex_levels(self.symbol),
                "bounce_score": await self.client.bounce_score(self.symbol),
                "conviction_symbol": await self.client.conviction(self.symbol),
                "long_term_quality": await self.client.long_term_quality(self.symbol),
                "politician_trades": await self.client.politician_trades(),
                "politician_trades_by_ticker": await self.client.politician_trades_by_ticker(
                    self.symbol
                ),
                "dividend_calendar": await self.client.dividend_calendar(),
                "economic_calendar": await self.client.economic_calendar(),
                "earnings_flow": await self.client.earnings_flow(),
                "ipo_scanner": await self.client.ipo_scanner(ipo_view),
                "ipo_scanner_view": ipo_view,
            }
        except TraderDaddyError as err:
            raise UpdateFailed(f"TraderDaddy Pro request failed: {err}") from err

        self.update_interval = (
            SCAN_INTERVAL_SLOW_OPEN if is_market_open() else SCAN_INTERVAL_SLOW_CLOSED
        )
        return data
