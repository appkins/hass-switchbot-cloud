"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientError,
)
from .const import DOMAIN, LOGGER
from .data import CatGenieDeviceStatusData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CatGenieUpdateCoordinator(DataUpdateCoordinator[CatGenieDeviceStatusData]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CatGenieApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=15),
            always_update=True,
        )

        self.client = client
        self.devices = {}

    async def _async_setup(self):
        """Set up the coordinator.

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        if self.client._access_token is None:
            await self.client.async_refresh_token()
        self.device = await self.client.async_get_first_device()  # devices.values()[0]

    async def _async_update_data(self) -> CatGenieDeviceStatusData:
        """Update data via library."""
        device_id = self.device["manufacturerId"]
        self.device_id = device_id

        try:
            result = await self.client.async_get_device_status(device_id)
            return CatGenieDeviceStatusData(
                state=result.get("state", 0),
                progress=result.get("progress", 0),
                error=result.get("error", ""),
                rtc=result.get("rtc", None),
                sens=result.get("sens", None),
                mode=result.get("mode", 0),
                manual=result.get("manual", 0),
                step_num=result.get("stepNum", 0),
                relay_mode=result.get("relayMode", None),
            )
        except CatGenieApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except CatGenieApiClientError as exception:
            raise UpdateFailed(exception) from exception
        except Exception as exception:
            raise f"Unknown error: {exception}" from exception
            # return CatGenieDeviceStatusData(

        # for device_id, device in self.devices.items():

        # return CatGenieDeviceStatusData(

        #     # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        #     # handled by the data update coordinator.
        #     async with async_timeout.timeout(10):
