"""TraderDaddy Pro sensors — fast-tier and slow-tier coordinators feed them all.

Each sensor reads from a coordinator's cached tool responses via a small
``value_fn`` (state) and optional ``attr_fn`` (extra attributes), so adding a
sensor is one description, no new polling. Fast-tier sensors bind to
``coordinator.py``'s market-wide/tracked-symbol vitals; slow-tier sensors
bind to ``coordinator_slow.py``'s screeners/calendars/heavier per-symbol
analytics.
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
from .entity import AnyTraderDaddyCoordinator, TraderDaddyEntity

# --- fast-tier extractors ----------------------------------------------------


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


def _health(data: dict) -> dict:
    return data.get("market_health") or {}


def _health_top_alert(data: dict) -> dict:
    signals = _health(data).get("signals") or []
    alerts = [s for s in signals if s.get("status") == "ALERT"]
    return alerts[0] if alerts else {}


def _institutional(data: dict) -> dict:
    return data.get("institutional_activity") or {}


def _institutional_top(data: dict) -> dict:
    flows = _institutional(data).get("flows") or []
    return flows[0] if flows else {}


def _conviction_market(data: dict) -> dict:
    return data.get("conviction") or {}


def _bounce_signals(data: dict) -> dict:
    return data.get("bounce_signals") or {}


def _bounce_top(data: dict) -> dict:
    signals = _bounce_signals(data).get("signals") or []
    return signals[0] if signals else {}


# --- slow-tier extractors -----------------------------------------------------


def _screener(data: dict) -> dict:
    return data.get("run_screener") or {}


def _screener_results(data: dict) -> list:
    return _screener(data).get("results") or []


def _strategy(data: dict) -> dict:
    return data.get("strategy_ideas") or {}


def _top_structure(data: dict) -> dict:
    structures = _strategy(data).get("structures") or []
    return structures[0] if structures else {}


def _edge_xray(data: dict) -> dict:
    return data.get("edge_xray") or {}


def _edge_summary(data: dict) -> dict:
    return _edge_xray(data).get("fairIvSummary") or {}


def _gex_ticker(data: dict) -> dict:
    return data.get("gex_ticker") or {}


def _apex(data: dict) -> dict:
    return data.get("apex_levels") or {}


def _apex_top(data: dict) -> dict:
    levels = _apex(data).get("levels") or []
    return levels[0] if levels else {}


def _bounce_score(data: dict) -> dict:
    return data.get("bounce_score") or {}


def _conviction_symbol(data: dict) -> dict:
    return data.get("conviction_symbol") or {}


def _quality(data: dict) -> dict:
    return data.get("long_term_quality") or {}


def _politician_trades(data: dict) -> dict:
    return data.get("politician_trades") or {}


def _politician_top(data: dict) -> dict:
    entries = _politician_trades(data).get("entries") or []
    return entries[0] if entries else {}


def _politician_by_ticker(data: dict) -> dict:
    return data.get("politician_trades_by_ticker") or {}


def _politician_ticker_latest(data: dict) -> dict:
    trades = _politician_by_ticker(data).get("trades") or []
    return trades[0] if trades else {}


def _dividends(data: dict) -> dict:
    return data.get("dividend_calendar") or {}


def _next_dividend(data: dict) -> dict:
    results = _dividends(data).get("results") or []
    return results[0] if results else {}


def _ipo(data: dict) -> dict:
    return data.get("ipo_scanner") or {}


def _ipo_top(data: dict) -> dict:
    rows = _ipo(data).get("data") or []
    return rows[0] if rows else {}


@dataclass(frozen=True, kw_only=True)
class TDSensorDescription(SensorEntityDescription):
    """Describes a TraderDaddy sensor with pure value/attribute extractors."""

    value_fn: Callable[[dict], StateType]
    attr_fn: Callable[[dict], dict[str, Any]] | None = None


FAST_SENSORS: tuple[TDSensorDescription, ...] = (
    TDSensorDescription(
        key="market_sentiment",
        translation_key="market_sentiment",
        icon="mdi:scale-balance",
        value_fn=lambda d: _stats(d).get("spy_sentiment"),
        attr_fn=lambda d: {
            "spy_put_call_ratio": _stats(d).get("spy_put_call_ratio"),
            "qqq_put_call_ratio": _stats(d).get("qqq_put_call_ratio"),
            "iwm_put_call_ratio": _stats(d).get("iwm_put_call_ratio"),
            "qqq_sentiment": _stats(d).get("qqq_sentiment"),
            "iwm_sentiment": _stats(d).get("iwm_sentiment"),
            "largest_trade_symbol": _stats(d).get("largest_trade_symbol"),
            "largest_trade_premium": _stats(d).get("largest_trade_premium"),
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
        value_fn=lambda d: (d.get("unusual_activity") or {}).get("aggregates", {}).get(
            "totalPremium"
        ),
    ),
    TDSensorDescription(
        key="market_health",
        translation_key="market_health",
        icon="mdi:heart-pulse",
        value_fn=lambda d: _health(d).get("compositeScore", {}).get("label"),
        attr_fn=lambda d: {
            "composite_value": _health(d).get("compositeScore", {}).get("value"),
            "composite_max": _health(d).get("compositeScore", {}).get("max"),
            "alert_count": _health(d).get("alertCount"),
            "watch_count": _health(d).get("watchCount"),
            "total_count": _health(d).get("totalCount"),
            "top_alert_label": _health_top_alert(d).get("label"),
            "top_alert_summary": _health_top_alert(d).get("summary"),
        },
    ),
    TDSensorDescription(
        key="institutional_leader",
        translation_key="institutional_leader",
        icon="mdi:bank",
        value_fn=lambda d: _institutional_top(d).get("ticker"),
        attr_fn=lambda d: {
            "sentiment": _institutional_top(d).get("sentiment"),
            "total_premium": _institutional_top(d).get("total_premium"),
            "flow_count": _institutional_top(d).get("flow_count"),
            "top5": [f.get("ticker") for f in (_institutional(d).get("flows") or [])[:5]],
        },
    ),
    TDSensorDescription(
        key="conviction_market",
        translation_key="conviction_market",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _conviction_market(d).get("score"),
        attr_fn=lambda d: {
            "top_tickers": [
                t.get("ticker") for t in (_conviction_market(d).get("topTickers") or [])
            ],
            "top_adds": [
                t.get("ticker") for t in (_conviction_market(d).get("topAdds") or [])
            ],
            "breakdown": _conviction_market(d).get("breakdown"),
            "as_of": _conviction_market(d).get("asOf"),
        },
    ),
    TDSensorDescription(
        key="bounce_signal_top",
        translation_key="bounce_signal_top",
        icon="mdi:trending-neutral",
        value_fn=lambda d: _bounce_top(d).get("ticker"),
        attr_fn=lambda d: {
            "signal_type": _bounce_top(d).get("signalType"),
            "price": _bounce_top(d).get("price"),
            "change_percent": _bounce_top(d).get("changePercent"),
            "composite_score": (_bounce_top(d).get("indicatorData") or {}).get(
                "compositeScore"
            ),
            "total": _bounce_signals(d).get("total"),
        },
    ),
)


SLOW_SENSORS: tuple[TDSensorDescription, ...] = (
    TDSensorDescription(
        key="featured_screener",
        translation_key="featured_screener",
        icon="mdi:filter-variant",
        value_fn=lambda d: _screener(d).get("screener", {}).get("name"),
        attr_fn=lambda d: {
            "screener_id": _screener(d).get("screener", {}).get("id"),
            "top_tickers": [r.get("ticker") for r in _screener_results(d)[:5]],
            "top_ticker": (_screener_results(d)[0].get("ticker") if _screener_results(d) else None),
            "count": _screener(d).get("count"),
            "returned": _screener(d).get("returned"),
        },
    ),
    TDSensorDescription(
        key="strategy_idea_top",
        translation_key="strategy_idea_top",
        icon="mdi:strategy",
        value_fn=lambda d: _top_structure(d).get("archetype"),
        attr_fn=lambda d: {
            "symbol": _strategy(d).get("symbol"),
            "direction": _strategy(d).get("direction"),
            "rank": _top_structure(d).get("rank"),
            "score": _top_structure(d).get("score"),
            "pop": _top_structure(d).get("pop"),
            "max_profit": _top_structure(d).get("maxProfit"),
            "max_loss": _top_structure(d).get("maxLoss"),
            "expiration": _top_structure(d).get("expiration"),
            "dte": _top_structure(d).get("dte"),
            "rationale": _top_structure(d).get("rationale"),
        },
    ),
    TDSensorDescription(
        key="edge_xray_bias",
        translation_key="edge_xray_bias",
        icon="mdi:radar",
        value_fn=lambda d: _edge_summary(d).get("overallBias"),
        attr_fn=lambda d: {
            "symbol": _edge_xray(d).get("symbol"),
            "spot": _edge_xray(d).get("spot"),
            "expiration": _edge_xray(d).get("expiration"),
            "dte": _edge_xray(d).get("dte"),
            "calls_median_residual": _edge_summary(d).get("callsMedianResidual"),
            "puts_median_residual": _edge_summary(d).get("putsMedianResidual"),
        },
    ),
    TDSensorDescription(
        key="gex_ticker_bias",
        translation_key="gex_ticker_bias",
        icon="mdi:gauge-full",
        value_fn=lambda d: _gex_ticker(d).get("bias"),
        attr_fn=lambda d: {
            "symbol": _gex_ticker(d).get("symbol"),
            "total_gex": _gex_ticker(d).get("totalGEX"),
            "flip_point": _gex_ticker(d).get("flipPoint"),
            "call_gex": _gex_ticker(d).get("callGex"),
            "put_gex": _gex_ticker(d).get("putGex"),
        },
    ),
    TDSensorDescription(
        key="apex_level_top",
        translation_key="apex_level_top",
        icon="mdi:magnet",
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _apex_top(d).get("strike"),
        attr_fn=lambda d: {
            "symbol": _apex(d).get("symbol"),
            "spot_price": _apex(d).get("spotPrice"),
            "gamma_flip": _apex(d).get("gammaFlip"),
            "score": _apex_top(d).get("score"),
            "net_gex": _apex_top(d).get("netGEX"),
        },
    ),
    TDSensorDescription(
        key="bounce_score_symbol",
        translation_key="bounce_score_symbol",
        icon="mdi:elevator-passenger",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _bounce_score(d).get("compositeScore"),
        attr_fn=lambda d: {
            "ticker": _bounce_score(d).get("ticker"),
            "price": _bounce_score(d).get("price"),
            "change_percent": _bounce_score(d).get("changePercent"),
            "rsi_value": _bounce_score(d).get("rsiValue"),
            "rsi_state": _bounce_score(d).get("rsiState"),
            "bb_state": _bounce_score(d).get("bbState"),
            "stoch_state": _bounce_score(d).get("stochState"),
        },
    ),
    TDSensorDescription(
        key="conviction_symbol",
        translation_key="conviction_symbol",
        icon="mdi:account-star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _conviction_symbol(d).get("score"),
        attr_fn=lambda d: {
            "ticker": _conviction_symbol(d).get("ticker"),
            "breakdown": _conviction_symbol(d).get("breakdown"),
            "as_of": _conviction_symbol(d).get("asOf"),
        },
    ),
    TDSensorDescription(
        key="long_term_quality",
        translation_key="long_term_quality",
        icon="mdi:diamond-stone",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _quality(d).get("qualityScore"),
        attr_fn=lambda d: {
            "symbol": _quality(d).get("symbol"),
            "sector": _quality(d).get("sector"),
            "pe": _quality(d).get("pe"),
            "roe": _quality(d).get("roe"),
            "dividend_yield": _quality(d).get("dividendYield"),
            "market_cap": _quality(d).get("marketCap"),
            "next_ex_date": _quality(d).get("nextExDate"),
            "next_earnings_date": _quality(d).get("nextEarningsDate"),
        },
    ),
    TDSensorDescription(
        key="politician_top_portfolio",
        translation_key="politician_top_portfolio",
        icon="mdi:bank-transfer",
        value_fn=lambda d: _politician_top(d).get("name"),
        attr_fn=lambda d: {
            "party": _politician_top(d).get("party"),
            "chamber": _politician_top(d).get("chamber"),
            "total_estimated": _politician_top(d).get("totalEstimated"),
            "trade_count": _politician_top(d).get("tradeCount"),
            "top_tickers": _politician_top(d).get("topTickers"),
            "tab": _politician_trades(d).get("tab"),
        },
    ),
    TDSensorDescription(
        key="politician_latest_trade",
        translation_key="politician_latest_trade",
        icon="mdi:gavel",
        value_fn=lambda d: _politician_ticker_latest(d).get("name"),
        attr_fn=lambda d: {
            "ticker": _politician_by_ticker(d).get("ticker"),
            "trade_type": _politician_ticker_latest(d).get("trade_type"),
            "trade_date": _politician_ticker_latest(d).get("trade_date"),
            "trade_amount": _politician_ticker_latest(d).get("trade_amount"),
            "party": _politician_ticker_latest(d).get("party"),
            "total_trades": _politician_by_ticker(d).get("total_trades"),
        },
    ),
    TDSensorDescription(
        key="next_dividend",
        translation_key="next_dividend",
        icon="mdi:cash-clock",
        value_fn=lambda d: _next_dividend(d).get("symbol"),
        attr_fn=lambda d: {
            "company_name": _next_dividend(d).get("companyName"),
            "ex_date": _next_dividend(d).get("exDate"),
            "pay_date": _next_dividend(d).get("payDate"),
            "dividend_rate": _next_dividend(d).get("dividendRate"),
            "dividend_yield": _next_dividend(d).get("dividendYield"),
            "count": _dividends(d).get("count"),
        },
    ),
    TDSensorDescription(
        key="ipo_highlight",
        translation_key="ipo_highlight",
        icon="mdi:rocket-launch",
        value_fn=lambda d: _ipo_top(d).get("company"),
        attr_fn=lambda d: {
            "view": d.get("ipo_scanner_view"),
            "symbol": _ipo_top(d).get("symbol"),
            "status": _ipo_top(d).get("status"),
            "expected_date": _ipo_top(d).get("expectedDate"),
            "source_count": _ipo(d).get("sourceCount"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the TraderDaddy Pro sensors — fast tier + slow tier."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        TraderDaddySensor(data["fast"], entry, description) for description in FAST_SENSORS
    ] + [
        TraderDaddySensor(data["slow"], entry, description) for description in SLOW_SENSORS
    ]
    async_add_entities(entities)


class TraderDaddySensor(TraderDaddyEntity, SensorEntity):
    """A single TraderDaddy Pro sensor, bound to either coordinator tier."""

    entity_description: TDSensorDescription

    def __init__(
        self,
        coordinator: AnyTraderDaddyCoordinator,
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
