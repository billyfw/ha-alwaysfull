"""The Always Full pet water bowl integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlwaysFullClient
from .const import DOMAIN
from .coordinator import AlwaysFullCoordinator, ha_utc_offset_hours

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import AlwaysFullConfigEntry

# Read platforms (`PARALLEL_UPDATES = 0`) and write platforms
# (`PARALLEL_UPDATES = 1`), in one list because Home Assistant forwards
# them together.
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]


async def async_setup_entry(hass: HomeAssistant, entry: AlwaysFullConfigEntry) -> bool:
    """Set up Always Full from a config entry."""
    client = AlwaysFullClient(
        async_get_clientsession(hass),
        token=entry.data.get(CONF_TOKEN, ""),
        # Home Assistant's configured zone, not the OS process's -- see
        # `ha_utc_offset_hours`. The coordinator re-syncs this every poll
        # so a DST transition does not need a restart.
        tz_offset_hours=ha_utc_offset_hours(),
    )

    coordinator = AlwaysFullCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _async_remove_left_out_devices(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AlwaysFullConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _bowl_ids(device: dr.DeviceEntry) -> set[str]:
    """Return the vendor device ids a registry device stands for (none for the account device)."""
    return {
        str(identifier)
        for domain, identifier in device.identifiers
        if domain == DOMAIN and not str(identifier).startswith("account_")
    }


@callback
def _async_remove_left_out_devices(
    hass: HomeAssistant, entry: AlwaysFullConfigEntry, coordinator: AlwaysFullCoordinator
) -> None:
    """Drop the device, and with it the entities, of every bowl the options leave out.

    A bowl left out AFTER it was set up would otherwise linger as a device
    with thirty-odd unavailable entities. The options flow reloads the
    entry, which brings setup back through here, so the device goes the
    moment the option is saved. Removing the config entry from the device
    rather than deleting the device outright is Home Assistant's own rule:
    the device is deleted when no other config entry claims it, which for a
    bowl is always.
    """
    if not coordinator.ignored:
        return
    registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if _bowl_ids(device) & coordinator.ignored:
            registry.async_update_device(device.id, remove_config_entry_id=entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: AlwaysFullConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow the user to delete a bowl's device once this entry no longer provides it.

    That is a bowl left out by the options, or one the vendor no longer
    lists on the account. A bowl that the last poll still reported stays,
    and so does the account device, which exists for as long as the entry
    does.
    """
    bowl_ids = _bowl_ids(device)
    if not bowl_ids:
        return False
    return not (bowl_ids & set(entry.runtime_data.data or {}))
