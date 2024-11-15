"""Constants for integration_blueprint."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN: Final[str] = "catgenie"
ATTRIBUTION: Final[str] = "Data provided by http://jsonplaceholder.typicode.com/"

HOST: Final[str] = "iot.petnovations.com"
ENDPOINT_REFRESH: Final[str] = "/facade/v1/mobile-user/refreshToken"
