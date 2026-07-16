"""Fast-tier DataUpdateCoordinator for TraderDaddy Pro.

One poll cycle fetches the market-wide vitals + the tracked symbol's core
reads, sequentially so the SDK's 429 backoff has room to work. Cadence
follows the US market: fast while open, slow off-hours. Shares one
``TraderDaddy`` client with the slow-tier coordinator (see
``coordinator_slow.py``) — that client is instantiated exactly once, in
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
    SCAN_INTERVAL_CLOSED,
    SCAN_INTERVAL_OPEN,
)

_LOGGER = logging.getLogger(__name__)


class TraderDaddyCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the fast-tier TraderDaddy Pro tool set on a market-hours cadence."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TraderDaddy) -> None:
        self.entry = entry
        self.client = client
        self.symbol = (
            entry.options.get(CONF_SYMBOL)
            or entry.data.get(CONF_SYMBOL)
            or DEFAULT_SYMBOL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_fast",
            update_interval=SCAN_INTERVAL_OPEN,
        )

    @property
    def is_demo(self) -> bool:
        return self.client.mock

    async def _async_update_data(self) -> dict:
        try:
            data = {
                "market_stats": await self.client.market_stats(),
                "unusual_activity": await self.client.unusual_activity(limit=10),
                "gex_overview": await self.client.gex_overview(),
                "iv_rank": await self.client.iv_rank(self.symbol),
                "sector_flow": await self.client.sector_flow(),
                "put_call_ratios": await self.client.put_call_ratios(self.symbol),
                "market_health": await self.client.market_health(),
                "institutional_activity": await self.client.institutional_activity(limit=10),
                "conviction": await self.client.conviction(),
                "bounce_signals": await self.client.bounce_signals(),
            }
        except TraderDaddyError as err:
            raise UpdateFailed(f"TraderDaddy Pro request failed: {err}") from err

        # Re-tune cadence for the next cycle based on the live market phase.
        self.update_interval = (
            SCAN_INTERVAL_OPEN if is_market_open() else SCAN_INTERVAL_CLOSED
        )
        return data
