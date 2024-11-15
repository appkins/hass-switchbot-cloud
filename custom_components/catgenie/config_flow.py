"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientCommunicationError,
    CatGenieApiClientError,
)
from .const import DOMAIN, LOGGER


class CatGenieHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    refresh_token=user_input[CONF_TOKEN],
                )
            except CatGenieApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except CatGenieApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except CatGenieApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, refresh_token: str) -> None:
        """Validate credentials."""
        client = CatGenieApiClient(
            refresh_token=refresh_token,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_devices()
