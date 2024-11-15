"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CatGenieDeviceStatusData:
    """Switchbot device data."""

    state: int = field(default_factory=int)
    progress: int = field(default_factory=int)
    error: str = field(default_factory=str)
    rtc: str | None = None
    sens: str | None = None
    mode: int = field(default_factory=int)
    manual: int = field(default_factory=int)
    step_num: int = field(default_factory=int)
    relay_mode: int | None = None


# @dataclass
# class CatGenieDevice:
#     """Switchbot devices data."""
#


# @dataclass
# class CatGenieDeviceStatusData:
#     """Data for the Cat Genie integration."""
#
