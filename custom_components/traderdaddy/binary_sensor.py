"""TraderDaddy Pro binary sensors — the automation triggers.

Each one flips ``on`` when a threshold tape/positioning condition is met, so
users can hang automations off them (flash a light, chime a speaker, wake an
e-ink panel) without polling anything themselves — they're pure reads off the
coordinators' cached dicts, same rule as the sensors.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ELEVATED_RISK_THRESHOLD, HIGH_CONVICTION_THRESHOLD
from .entity import AnyTraderDaddyCoordinator, TraderDaddyEntity

_LEGENDARY = "LEGENDARY"
_SHORT_GAMMA = "SHORT_GAMMA"


@dataclass(frozen=True, kw_only=True)
class TDBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description bound to a coordinator's cached dict."""

    is_on_fn: Callable[[dict], bool]
    attr_fn: Callable[[dict], dict[str, Any]] | None = None


def _legendary_rows(data: dict) -> list[dict]:
    rows = (data.get("unusual_activity") or {}).get("data") or []
    return [r for r in rows if r.get("tier") == _LEGENDARY]


def _gex_market_summary(data: dict) -> dict:
    return (data.get("gex_overview") or {}).get("marketSummary") or {}


def _health(data: dict) -> dict:
    return data.get("market_health") or {}


def _bounce_signals(data: dict) -> list:
    return (data.get("bounce_signals") or {}).get("signals") or []


def _conviction_market(data: dict) -> dict:
    return data.get("conviction") or {}


FAST_BINARY_SENSORS: tuple[TDBinarySensorDescription, ...] = (
    TDBinarySensorDescription(
        key="legendary_print",
        translation_key="legendary_print",
        icon="mdi:star-shooting",
        is_on_fn=lambda d: bool(_legendary_rows(d)),
        attr_fn=lambda d: {
            "count": len(_legendary_rows(d)),
            "tickers": [r.get("ticker") for r in _legendary_rows(d)],
            "top_ticker": _legendary_rows(d)[0].get("ticker") if _legendary_rows(d) else None,
            "top_premium": _legendary_rows(d)[0].get("premium") if _legendary_rows(d) else None,
        },
    ),
    TDBinarySensorDescription(
        key="gamma_flip",
        translation_key="gamma_flip",
        icon="mdi:swap-vertical-bold",
        is_on_fn=lambda d: _gex_market_summary(d).get("bias") == _SHORT_GAMMA,
        attr_fn=lambda d: {
            "bias": _gex_market_summary(d).get("bias"),
            "total_gex": _gex_market_summary(d).get("totalGEX"),
            "interpretation": _gex_market_summary(d).get("interpretation"),
        },
    ),
    TDBinarySensorDescription(
        key="elevated_risk",
        translation_key="elevated_risk",
        icon="mdi:alert-octagon",
        is_on_fn=lambda d: _health(d).get("alertCount", 0) >= ELEVATED_RISK_THRESHOLD,
        attr_fn=lambda d: {
            "alert_count": _health(d).get("alertCount"),
            "watch_count": _health(d).get("watchCount"),
            "total_count": _health(d).get("totalCount"),
        },
    ),
    TDBinarySensorDescription(
        key="bounce_signal",
        translation_key="bounce_signal",
        icon="mdi:trending-up",
        is_on_fn=lambda d: bool(_bounce_signals(d)),
        attr_fn=lambda d: {
            "count": len(_bounce_signals(d)),
            "top_ticker": _bounce_signals(d)[0].get("ticker") if _bounce_signals(d) else None,
        },
    ),
    TDBinarySensorDescription(
        key="high_conviction",
        translation_key="high_conviction",
        icon="mdi:target",
        is_on_fn=lambda d: _conviction_market(d).get("score", 0) >= HIGH_CONVICTION_THRESHOLD,
        attr_fn=lambda d: {
            "score": _conviction_market(d).get("score"),
            "top_tickers": [
                t.get("ticker") for t in (_conviction_market(d).get("topTickers") or [])
            ],
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TraderDaddy Pro binary sensors — all fast-tier."""
    data = hass.data[DOMAIN][entry.entry_id]
    fast = data["fast"]
    async_add_entities(
        TraderDaddyBinarySensor(fast, entry, description) for description in FAST_BINARY_SENSORS
    )


class TraderDaddyBinarySensor(TraderDaddyEntity, BinarySensorEntity):
    """Generic binary sensor over a coordinator's cached dict."""

    entity_description: TDBinarySensorDescription

    def __init__(
        self,
        coordinator: AnyTraderDaddyCoordinator,
        entry: ConfigEntry,
        description: TDBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
