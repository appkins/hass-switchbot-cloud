"""Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/integration_blueprint
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import hdrs
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import CatGenieApiClient
from .const import DOMAIN, HOST
from .coordinator import CatGenieUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .data import CatGenieDeviceStatusData


PLATFORMS: list[Platform] = [
    # Platform.SENSOR,
    Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[CatGenieDeviceStatusData],
) -> bool:
    """Set up this integration using UI."""
    coordinator = CatGenieUpdateCoordinator(
        hass=hass,
        client=CatGenieApiClient(
            refresh_token=entry.data[CONF_TOKEN],
            session=async_create_clientsession(
                hass,
                base_url=f"https://{HOST}",
                headers={
                    hdrs.HOST: HOST,
                    hdrs.USER_AGENT: "CatGenie/493 CFNetwork/1559 Darwin/24.0.0",
                    hdrs.CONNECTION: "keep-alive",
                    hdrs.ACCEPT: "application/json, text/plain, */*",
                    hdrs.ACCEPT_ENCODING: "gzip, deflate, br",
                    hdrs.ACCEPT_LANGUAGE: "en-US,en;q=0.9",
                },
            ),
        ),
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = {
        "coordinator": coordinator,
    }

    # async_add_entities(
    #     CatGenieEntity(coordinator, idx) for idx, ent in enumerate(coordinator.data)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
