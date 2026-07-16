"""Shared base entity for TraderDaddy Pro."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TraderDaddyCoordinator
from .coordinator_slow import TraderDaddySlowCoordinator

AnyTraderDaddyCoordinator = TraderDaddyCoordinator | TraderDaddySlowCoordinator


class TraderDaddyEntity(CoordinatorEntity[AnyTraderDaddyCoordinator]):
    """Base entity — attaches every sensor to one service device.

    Works with either the fast or the slow coordinator; both expose the same
    ``.data`` dict shape (a cache of tool responses) that ``value_fn``/
    ``attr_fn`` callables read from.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AnyTraderDaddyCoordinator, entry: ConfigEntry, key: str
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
