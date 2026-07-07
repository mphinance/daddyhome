"""DataUpdateCoordinator for TraderDaddy Pro.

One poll cycle fetches the handful of tools the sensors need, sequentially so
the SDK's 429 backoff has room to work. Cadence follows the US market: fast
while open, slow off-hours.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from traderdaddy import TraderDaddy, TraderDaddyError, is_market_open

from .const import (
    CONF_API_KEY,
    CONF_SYMBOL,
    DEFAULT_SYMBOL,
    DOMAIN,
    SCAN_INTERVAL_CLOSED,
    SCAN_INTERVAL_OPEN,
)

_LOGGER = logging.getLogger(__name__)


class TraderDaddyCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the TraderDaddy Pro tool set on a market-hours cadence."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.symbol = (
            entry.options.get(CONF_SYMBOL)
            or entry.data.get(CONF_SYMBOL)
            or DEFAULT_SYMBOL
        )

        api_key = entry.data.get(CONF_API_KEY)
        if api_key:
            # Share Home Assistant's httpx client rather than spinning up our own.
            self.client = TraderDaddy(api_key=api_key, client=get_async_client(hass))
        else:
            # No key → keyless demo mode (the funnel default).
            self.client = TraderDaddy(mock=True)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
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
            }
        except TraderDaddyError as err:
            raise UpdateFailed(f"TraderDaddy Pro request failed: {err}") from err

        # Re-tune cadence for the next cycle based on the live market phase.
        self.update_interval = (
            SCAN_INTERVAL_OPEN if is_market_open() else SCAN_INTERVAL_CLOSED
        )
        return data

    async def async_close(self) -> None:
        await self.client.aclose()
