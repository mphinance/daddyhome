"""Config + options flow for TraderDaddy Pro.

The API key is optional: leave it blank to run in keyless demo mode (typed
fixtures, no network). Provide a ``td_live_`` key to go live — it's validated
with a single call before the entry is created.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.httpx_client import get_async_client
from traderdaddy import TraderDaddy, TraderDaddyError

from .const import CONF_API_KEY, CONF_SYMBOL, DEFAULT_SYMBOL, DOMAIN


class TraderDaddyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # Single instance — the device groups every sensor.
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = (user_input.get(CONF_API_KEY) or "").strip()
            symbol = (user_input.get(CONF_SYMBOL) or DEFAULT_SYMBOL).strip().upper()
            symbol = symbol or DEFAULT_SYMBOL

            if api_key:
                try:
                    td = TraderDaddy(
                        api_key=api_key, client=get_async_client(self.hass)
                    )
                    await td.market_stats()
                    await td.aclose()
                except TraderDaddyError:
                    errors["base"] = "cannot_connect"

            if not errors:
                title = "TraderDaddy Pro" if api_key else "TraderDaddy Pro (demo)"
                return self.async_create_entry(
                    title=title,
                    data={CONF_API_KEY: api_key, CONF_SYMBOL: symbol},
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Optional(CONF_SYMBOL, default=DEFAULT_SYMBOL): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return TraderDaddyOptionsFlow()


class TraderDaddyOptionsFlow(OptionsFlow):
    """Let the user change the tracked symbol without re-adding the entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            symbol = (user_input.get(CONF_SYMBOL) or DEFAULT_SYMBOL).strip().upper()
            return self.async_create_entry(
                title="", data={CONF_SYMBOL: symbol or DEFAULT_SYMBOL}
            )

        current = (
            self.config_entry.options.get(CONF_SYMBOL)
            or self.config_entry.data.get(CONF_SYMBOL)
            or DEFAULT_SYMBOL
        )
        schema = vol.Schema({vol.Optional(CONF_SYMBOL, default=current): str})
        return self.async_show_form(step_id="init", data_schema=schema)
