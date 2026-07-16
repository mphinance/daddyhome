"""TraderDaddy Pro events — fires once per genuinely-new item on the tape.

Generalizes ``binary_sensor.td_legendary_print`` (which only ever reflects
"is there one right now") into HA's ``event`` platform: each entity tracks
the ids it has already seen and fires ``EventEntity`` state changes only for
items that are new since the last poll. On first load every currently-cached
id is marked seen (so a fresh install doesn't fire a burst of "new" events
for data that was already on the tape) — only items that arrive on a
*subsequent* coordinator refresh trigger.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AnyTraderDaddyCoordinator, TraderDaddyEntity

_EVENT_TYPE = "new_item"


@dataclass(frozen=True, kw_only=True)
class TDEventDescription(EventEntityDescription):
    """Event description: pulls a list of items + a stable id per item."""

    tier: str  # "fast" or "slow"
    items_fn: Callable[[dict], list[dict]]
    id_fn: Callable[[dict], str | None]
    attr_fn: Callable[[dict], dict[str, Any]]


def _unusual_rows(data: dict) -> list[dict]:
    return (data.get("unusual_activity") or {}).get("data") or []


def _politician_trades(data: dict) -> list[dict]:
    return (data.get("politician_trades_by_ticker") or {}).get("trades") or []


def _ipo_rows(data: dict) -> list[dict]:
    return (data.get("ipo_scanner") or {}).get("data") or []


def _earnings_items(data: dict) -> list[dict]:
    return (data.get("earnings_flow") or {}).get("earnings") or []


EVENT_DESCRIPTIONS: tuple[TDEventDescription, ...] = (
    TDEventDescription(
        key="new_print",
        translation_key="new_print",
        icon="mdi:flash",
        tier="fast",
        event_types=[_EVENT_TYPE],
        items_fn=_unusual_rows,
        id_fn=lambda r: r.get("id"),
        attr_fn=lambda r: {
            "ticker": r.get("ticker"),
            "tier": r.get("tier"),
            "premium": r.get("premium"),
            "sentiment": r.get("sentiment"),
            "flow_description": r.get("flowDescription"),
        },
    ),
    TDEventDescription(
        key="new_politician_trade",
        translation_key="new_politician_trade",
        icon="mdi:bank",
        tier="slow",
        event_types=[_EVENT_TYPE],
        items_fn=_politician_trades,
        id_fn=lambda r: r.get("id"),
        attr_fn=lambda r: {
            "name": r.get("name"),
            "party": r.get("party"),
            "ticker": r.get("ticker"),
            "trade_type": r.get("trade_type"),
            "trade_amount": r.get("trade_amount"),
        },
    ),
    TDEventDescription(
        key="new_ipo_listing",
        translation_key="new_ipo_listing",
        icon="mdi:rocket-launch",
        tier="slow",
        event_types=[_EVENT_TYPE],
        items_fn=_ipo_rows,
        id_fn=lambda r: str(r.get("id")) if r.get("id") is not None else r.get("companyKey"),
        attr_fn=lambda r: {
            "company": r.get("company"),
            "symbol": r.get("symbol"),
            "exchange": r.get("exchange"),
            "status": r.get("status"),
        },
    ),
    TDEventDescription(
        key="earnings_approaching",
        translation_key="earnings_approaching",
        icon="mdi:calendar-alert",
        tier="slow",
        event_types=[_EVENT_TYPE],
        items_fn=_earnings_items,
        id_fn=lambda item: (
            f"{(item.get('event') or {}).get('symbol')}:{(item.get('event') or {}).get('earningsDate')}"
            if item.get("event")
            else None
        ),
        attr_fn=lambda item: {
            "symbol": (item.get("event") or {}).get("symbol"),
            "earnings_date": (item.get("event") or {}).get("earningsDate"),
            "earnings_time": (item.get("event") or {}).get("earningsTime"),
            "expected_move_pct": (item.get("event") or {}).get("expectedMovePct"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TraderDaddy Pro event entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        TraderDaddyEventEntity(data[description.tier], entry, description)
        for description in EVENT_DESCRIPTIONS
    ]
    async_add_entities(entities)


class TraderDaddyEventEntity(TraderDaddyEntity, EventEntity):
    """Fires ``new_item`` once per id not previously seen by this entity."""

    entity_description: TDEventDescription

    def __init__(
        self,
        coordinator: AnyTraderDaddyCoordinator,
        entry: ConfigEntry,
        description: TDEventDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description
        self._seen: set[str] = set()
        self._primed = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._scan(prime=True)

    def _handle_coordinator_update(self) -> None:
        self._scan(prime=False)
        super()._handle_coordinator_update()

    def _scan(self, *, prime: bool) -> None:
        items = self.entity_description.items_fn(self.coordinator.data)
        newly_seen: list[dict] = []
        for item in items:
            item_id = self.entity_description.id_fn(item)
            if item_id is None or item_id in self._seen:
                continue
            self._seen.add(item_id)
            if not prime:
                newly_seen.append(item)

        if prime:
            self._primed = True
            return

        if newly_seen:
            latest = newly_seen[0]
            self._trigger_event(_EVENT_TYPE, self.entity_description.attr_fn(latest))
