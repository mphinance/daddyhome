"""The TraderDaddy Pro integration — market flow as Home Assistant sensors."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers.httpx_client import get_async_client
from traderdaddy import TraderDaddy, TraderDaddyError

from .const import CONF_API_KEY, CONF_SYMBOL, DEFAULT_SYMBOL, DOMAIN, PLATFORMS
from .coordinator import TraderDaddyCoordinator
from .coordinator_slow import TraderDaddySlowCoordinator

SERVICE_HEDGE_ANALYSIS = "hedge_analysis"

_HEDGE_ANALYSIS_SCHEMA = vol.Schema(
    {
        vol.Required("symbol"): str,
        vol.Required("shares"): vol.Coerce(int),
        vol.Optional("basis"): vol.Coerce(float),
        vol.Optional("atr"): vol.Coerce(float),
        vol.Optional("limit"): vol.Coerce(int),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TraderDaddy Pro from a config entry."""
    # One SDK instance, shared by both coordinators (fast + slow tiers).
    api_key = entry.data.get(CONF_API_KEY)
    if api_key:
        client = TraderDaddy(api_key=api_key, client=get_async_client(hass))
    else:
        client = TraderDaddy(mock=True)  # keyless demo mode

    fast = TraderDaddyCoordinator(hass, entry, client)
    slow = TraderDaddySlowCoordinator(hass, entry, client)
    await fast.async_config_entry_first_refresh()
    await slow.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "fast": fast,
        "slow": slow,
        "client": client,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_HEDGE_ANALYSIS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_HEDGE_ANALYSIS,
            _make_hedge_analysis_handler(hass),
            schema=_HEDGE_ANALYSIS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["client"].aclose()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_HEDGE_ANALYSIS)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options (e.g. the tracked symbol) change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _make_hedge_analysis_handler(hass: HomeAssistant):
    """On-demand hedge_analysis — needs call-time args, so it's a service
    rather than a polled sensor. Uses the first (only, single-instance)
    entry's shared client.
    """

    async def _handler(call: ServiceCall) -> ServiceResponse:
        entries = hass.data.get(DOMAIN) or {}
        if not entries:
            raise RuntimeError("TraderDaddy Pro is not configured")
        client: TraderDaddy = next(iter(entries.values()))["client"]

        kwargs: dict[str, Any] = {}
        for key in ("basis", "atr", "limit"):
            if key in call.data:
                kwargs[key] = call.data[key]

        try:
            result = await client.hedge_analysis(
                call.data["symbol"], call.data["shares"], **kwargs
            )
        except TraderDaddyError as err:
            raise RuntimeError(f"TraderDaddy Pro request failed: {err}") from err

        return result

    return _handler
