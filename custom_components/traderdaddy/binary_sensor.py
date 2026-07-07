"""TraderDaddy Pro binary sensor — the LEGENDARY-print trigger.

``binary_sensor.td_legendary_print`` turns on whenever a top-tier (LEGENDARY)
unusual-options print is on the tape. This is the entity to hang an automation
off — flash a light, chime a speaker, wake an e-ink panel.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TraderDaddyCoordinator
from .entity import TraderDaddyEntity

_LEGENDARY = "LEGENDARY"

DESCRIPTION = BinarySensorEntityDescription(
    key="legendary_print",
    translation_key="legendary_print",
    icon="mdi:star-shooting",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the LEGENDARY-print binary sensor."""
    coordinator: TraderDaddyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LegendaryPrintBinarySensor(coordinator, entry)])


class LegendaryPrintBinarySensor(TraderDaddyEntity, BinarySensorEntity):
    """On when a LEGENDARY-tier print is on the current tape."""

    entity_description = DESCRIPTION

    def __init__(
        self, coordinator: TraderDaddyCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, DESCRIPTION.key)
        self.entity_description = DESCRIPTION

    def _legendary_rows(self) -> list[dict]:
        rows = (self.coordinator.data.get("unusual_activity") or {}).get("data") or []
        return [r for r in rows if r.get("tier") == _LEGENDARY]

    @property
    def is_on(self) -> bool:
        return bool(self._legendary_rows())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        rows = self._legendary_rows()
        return {
            "count": len(rows),
            "tickers": [r.get("ticker") for r in rows],
            "top_ticker": rows[0].get("ticker") if rows else None,
            "top_premium": rows[0].get("premium") if rows else None,
        }
