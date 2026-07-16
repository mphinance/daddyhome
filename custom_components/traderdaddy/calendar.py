"""TraderDaddy Pro calendars — economic, earnings, and dividend dates as
native HA ``calendar`` entities (shows up in the HA calendar dashboard and is
usable in automations/templates without a helper sensor).

Pure reads off the slow-tier coordinator's cached dict, converted to
``CalendarEvent`` on demand — no extra polling.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityDescription,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator_slow import TraderDaddySlowCoordinator
from .entity import TraderDaddyEntity


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


@dataclass(frozen=True, kw_only=True)
class TDCalendarDescription(CalendarEntityDescription):
    """Calendar description: pulls raw rows + converts one row to an event."""

    rows_fn: Callable[[dict], list[dict]]
    to_event_fn: Callable[[dict], CalendarEvent | None]


def _economic_rows(data: dict) -> list[dict]:
    return (data.get("economic_calendar") or {}).get("events") or []


def _economic_event(row: dict) -> CalendarEvent | None:
    day = _parse_date(row.get("date"))
    if day is None:
        return None
    summary = f"{row.get('country', '')} {row.get('event', 'Economic event')}".strip()
    return CalendarEvent(
        start=day,
        end=day + timedelta(days=1),
        summary=summary,
        description=(
            f"Impact: {row.get('impact')}\n"
            f"Forecast: {row.get('forecast')}\n"
            f"Previous: {row.get('previous')}\n"
            f"Actual: {row.get('actual')}"
        ),
    )


def _earnings_rows(data: dict) -> list[dict]:
    items = (data.get("earnings_flow") or {}).get("earnings") or []
    return [item.get("event") for item in items if item.get("event")]


def _earnings_event(row: dict) -> CalendarEvent | None:
    day = _parse_date(row.get("earningsDate"))
    if day is None:
        return None
    return CalendarEvent(
        start=day,
        end=day + timedelta(days=1),
        summary=f"{row.get('symbol')} earnings ({row.get('earningsTime', '?')})",
        description=(
            f"Expected move: {row.get('expectedMovePct')}%\n"
            f"Pre-earnings sentiment: {row.get('preEarningsSentiment')}\n"
            f"Consensus confidence: {row.get('consensusConfidence')}"
        ),
    )


def _dividend_rows(data: dict) -> list[dict]:
    return (data.get("dividend_calendar") or {}).get("results") or []


def _dividend_event(row: dict) -> CalendarEvent | None:
    day = _parse_date(row.get("exDate"))
    if day is None:
        return None
    return CalendarEvent(
        start=day,
        end=day + timedelta(days=1),
        summary=f"{row.get('symbol')} ex-dividend (${row.get('dividendRate')})",
        description=(
            f"{row.get('companyName')} ({row.get('sector')})\n"
            f"Yield: {row.get('dividendYield')}%\n"
            f"Pay date: {row.get('payDate')}"
        ),
    )


CALENDAR_DESCRIPTIONS: tuple[TDCalendarDescription, ...] = (
    TDCalendarDescription(
        key="economic_calendar",
        translation_key="economic_calendar",
        icon="mdi:calendar-clock",
        rows_fn=_economic_rows,
        to_event_fn=_economic_event,
    ),
    TDCalendarDescription(
        key="earnings_calendar",
        translation_key="earnings_calendar",
        icon="mdi:calendar-star",
        rows_fn=_earnings_rows,
        to_event_fn=_earnings_event,
    ),
    TDCalendarDescription(
        key="dividend_calendar",
        translation_key="dividend_calendar",
        icon="mdi:calendar-cash",
        rows_fn=_dividend_rows,
        to_event_fn=_dividend_event,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TraderDaddy Pro calendars — all slow-tier."""
    data = hass.data[DOMAIN][entry.entry_id]
    slow = data["slow"]
    async_add_entities(
        TraderDaddyCalendar(slow, entry, description) for description in CALENDAR_DESCRIPTIONS
    )


class TraderDaddyCalendar(TraderDaddyEntity, CalendarEntity):
    """Generic read-only calendar over a slow-tier tool's rows."""

    entity_description: TDCalendarDescription

    def __init__(
        self,
        coordinator: TraderDaddySlowCoordinator,
        entry: ConfigEntry,
        description: TDCalendarDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    def _all_events(self) -> list[CalendarEvent]:
        rows = self.entity_description.rows_fn(self.coordinator.data)
        events = [self.entity_description.to_event_fn(row) for row in rows]
        return sorted((e for e in events if e is not None), key=lambda e: e.start_datetime_local)

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now().date()
        for event in self._all_events():
            end = event.end if isinstance(event.end, date) else event.end.date()
            if end >= now:
                return event
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        start = start_date.date()
        end = end_date.date()
        return [event for event in self._all_events() if start <= event.start_datetime_local.date() <= end]
