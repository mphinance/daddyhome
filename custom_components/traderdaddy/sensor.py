"""TraderDaddy Pro sensors — one poll cycle feeds them all.

Each sensor reads from the coordinator's cached tool responses via a small
``value_fn`` (state) and optional ``attr_fn`` (extra attributes), so adding a
sensor is one description, no new polling.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import TraderDaddyCoordinator
from .entity import TraderDaddyEntity


def _stats(data: dict) -> dict:
    return data.get("market_stats") or {}


def _top_flow(data: dict) -> dict:
    rows = (data.get("unusual_activity") or {}).get("data") or []
    return rows[0] if rows else {}


def _summary(data: dict) -> dict:
    return (data.get("gex_overview") or {}).get("marketSummary") or {}


def _iv(data: dict) -> dict:
    return data.get("iv_rank") or {}


def _macro(data: dict) -> dict:
    return (data.get("sector_flow") or {}).get("macro") or {}


def _pcr(data: dict) -> dict:
    return data.get("put_call_ratios") or {}


@dataclass(frozen=True, kw_only=True)
class TDSensorDescription(SensorEntityDescription):
    """Describes a TraderDaddy sensor with pure value/attribute extractors."""

    value_fn: Callable[[dict], StateType]
    attr_fn: Callable[[dict], dict[str, Any]] | None = None


SENSORS: tuple[TDSensorDescription, ...] = (
    TDSensorDescription(
        key="market_sentiment",
        translation_key="market_sentiment",
        icon="mdi:scale-balance",
        value_fn=lambda d: _stats(d).get("overallSentiment"),
        attr_fn=lambda d: {
            "sentiment_score": _stats(d).get("sentimentScore"),
            "bullish_bearish_ratio": _stats(d).get("bullishBearishRatio"),
            "total_bullish_premium": _stats(d).get("totalBullishPremium"),
            "total_bearish_premium": _stats(d).get("totalBearishPremium"),
            "dominant_flow": _stats(d).get("dominantFlow"),
        },
    ),
    TDSensorDescription(
        key="put_call_ratio",
        translation_key="put_call_ratio",
        icon="mdi:call-split",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _pcr(d).get("putCallRatio"),
        attr_fn=lambda d: {
            "ticker": _pcr(d).get("ticker"),
            "put_volume": _pcr(d).get("putVolume"),
            "call_volume": _pcr(d).get("callVolume"),
            "sentiment": _pcr(d).get("sentiment"),
            "expiration_date": _pcr(d).get("expirationDate"),
        },
    ),
    TDSensorDescription(
        key="gamma_bias",
        translation_key="gamma_bias",
        icon="mdi:gauge",
        value_fn=lambda d: _summary(d).get("bias"),
        attr_fn=lambda d: {
            "total_gex": _summary(d).get("totalGEX"),
            "interpretation": _summary(d).get("interpretation"),
        },
    ),
    TDSensorDescription(
        key="iv_rank",
        translation_key="iv_rank",
        icon="mdi:chart-bell-curve",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _iv(d).get("ivRank"),
        attr_fn=lambda d: {
            "symbol": _iv(d).get("symbol"),
            "iv_percentile": _iv(d).get("ivPercentile"),
            "current_iv": _iv(d).get("currentIV"),
            "interpretation": _iv(d).get("interpretation"),
            "note": _iv(d).get("note"),
        },
    ),
    TDSensorDescription(
        key="sector_leader",
        translation_key="sector_leader",
        icon="mdi:podium-gold",
        value_fn=lambda d: _macro(d).get("dominantSector"),
        attr_fn=lambda d: {
            "risk_on_score": _macro(d).get("riskOnScore"),
            "dominant_flow": _macro(d).get("dominantFlow"),
            "label": _macro(d).get("label"),
            "description": _macro(d).get("description"),
        },
    ),
    TDSensorDescription(
        key="top_flow",
        translation_key="top_flow",
        icon="mdi:fire",
        value_fn=lambda d: _top_flow(d).get("ticker"),
        attr_fn=lambda d: {
            "premium": _top_flow(d).get("premium"),
            "type": _top_flow(d).get("type"),
            "tier": _top_flow(d).get("tier"),
            "sentiment": _top_flow(d).get("sentiment"),
            "score": _top_flow(d).get("score"),
            "flow_description": _top_flow(d).get("flowDescription"),
        },
    ),
    TDSensorDescription(
        key="total_flow_premium",
        translation_key="total_flow_premium",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="USD",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda d: _stats(d).get("totalFlowPremium"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the TraderDaddy Pro sensors."""
    coordinator: TraderDaddyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TraderDaddySensor(coordinator, entry, description) for description in SENSORS
    )


class TraderDaddySensor(TraderDaddyEntity, SensorEntity):
    """A single TraderDaddy Pro sensor."""

    entity_description: TDSensorDescription

    def __init__(
        self,
        coordinator: TraderDaddyCoordinator,
        entry: ConfigEntry,
        description: TDSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
