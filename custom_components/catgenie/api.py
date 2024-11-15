"""Sample API Client."""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any

import aiohttp
import async_timeout


class CatGenieApiClientError(Exception):
    """Exception to indicate a general API error."""


class CatGenieApiClientCommunicationError(
    CatGenieApiClientError,
):
    """Exception to indicate a communication error."""


class CatGenieApiClientAuthenticationError(
    CatGenieApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise CatGenieApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class CatGenieApiClient:
    """Sample API Client."""

    def __init__(
        self,
        refresh_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._refresh_token = refresh_token
        self._access_token = None
        self._session = session
        self._token_expiration = datetime.now(timezone.utc)

    async def async_get_first_device(self) -> Any:
        """Get data from the API."""
        resp = await self.async_get_devices()
        return resp[0]

    async def async_get_devices(self) -> list:
        """Obtain the list of devices associated to a user."""
        resp = await self._api_wrapper(
            aiohttp.hdrs.METH_GET,
            url="/device/device",
        )
        return resp["thingList"]

    async def async_get_device_status(self, device_id) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_GET,
            url=f"/device/management/{device_id}/operation/status",
        )

    async def async_device_operation(self, device_id, state: int = 1) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_POST,
            url=f"/device/management/{device_id}/operation",
            data={"state": state},
        )

    def _is_token_expired(self) -> bool:
        """Check if the token is expired."""
        if self._access_token is None:
            return True
        return self._token_expiration >= datetime.now(timezone.utc)

    @property
    def headers(self) -> dict:
        """Return the access token."""
        if self._access_token is not None:
            return { aiohttp.hdrs.AUTHORIZATION: f"Bearer {self._access_token}"}
        return {}

    async def async_refresh_token(self) -> None:
        """Obtain a valid access token."""
        if self._access_token is not None:
            self._access_token = None

        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    url="/facade/v1/mobile-user/refreshToken",
                    json={"refreshToken": self._refresh_token},
                    headers=self.headers,
                )
                _verify_response_or_raise(response)

                data = await response.json()

                expiration = data["expiration"]
                access_token = data["token"]

                self._access_token = access_token

                self._token_expiration = datetime.fromtimestamp(
                    float(int(expiration) / 1000),
                    timezone.utc,
                )
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Error refreshing token - {exception}"
            raise CatGenieApiClientError(
                msg,
            ) from exception

    async def _api_wrapper_inner(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        real_headers = self.headers
        if headers is not None:
            real_headers.update(headers)

        async with async_timeout.timeout(10):
            response = await self._session.request(
                method=method,
                url=url,
                headers=real_headers,
                json=data,
            )
            _verify_response_or_raise(response)
            return await response.json()

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        if self._is_token_expired():
            await self.async_refresh_token()

        try:
            return await self._api_wrapper_inner(
                method=method,
                url=url,
                data=data,
                headers=headers,
            )
        except CatGenieApiClientAuthenticationError:
            try:
                await self.async_refresh_token()
                return await self._api_wrapper_inner(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                )
            except Exception as exception:  # pylint: disable=broad-except
                msg = f"Something really wrong happened! - {exception}"
                raise CatGenieApiClientError(
                    msg,
                ) from exception
        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise CatGenieApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise CatGenieApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise CatGenieApiClientError(
                msg,
            ) from exception
