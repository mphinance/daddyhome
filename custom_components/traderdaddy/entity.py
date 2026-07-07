"""Shared base entity for TraderDaddy Pro."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TraderDaddyCoordinator


class TraderDaddyEntity(CoordinatorEntity[TraderDaddyCoordinator]):
    """Base entity — attaches every sensor to one service device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: TraderDaddyCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TraderDaddy Pro",
            manufacturer="TraderDaddy Pro",
            model="MCP flow feed",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://traderdaddy.pro",
        )
