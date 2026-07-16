"""Diagnostics support for TraderDaddy Pro.

Downloadable from Settings -> Devices & Services -> TraderDaddy Pro -> ⋮ ->
Download diagnostics. Dumps the config entry (API key redacted) plus both
coordinators' cached data, for bug reports.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "fast_coordinator": {
            "last_update_success": data["fast"].last_update_success,
            "update_interval": str(data["fast"].update_interval),
            "data": data["fast"].data,
        },
        "slow_coordinator": {
            "last_update_success": data["slow"].last_update_success,
            "update_interval": str(data["slow"].update_interval),
            "data": data["slow"].data,
        },
    }
