"""Support for SwitchBot vacuum."""

from typing import Any, ClassVar
import typing

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from switchbot_api import Device, Remote, SwitchBotAPI, VacuumCommands

from . import SwitchbotCloudData
from .const import (
    DOMAIN,
    VACUUM_FAN_SPEED_MAX,
    VACUUM_FAN_SPEED_QUIET,
    VACUUM_FAN_SPEED_STANDARD,
    VACUUM_FAN_SPEED_STRONG,
)
from .coordinator import SwitchBotCoordinator
from .entity import SwitchBotCloudEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SwitchBot Cloud entry."""
    data: SwitchbotCloudData = hass.data[DOMAIN][config.entry_id]
    async_add_entities(
        _async_make_entity(data.api, device, coordinator)
        for device, coordinator in data.devices.vacuums
    )


VACUUM_SWITCHBOT_STATE_TO_HA_STATE: dict[str, str] = {
    "StandBy": STATE_IDLE,
    "Clearing": STATE_CLEANING,
    "Paused": STATE_PAUSED,
    "GotoChargeBase": STATE_RETURNING,
    "Charging": STATE_DOCKED,
    "ChargeDone": STATE_DOCKED,
    "Dormant": STATE_IDLE,
    "InTrouble": STATE_ERROR,
    "InRemoteControl": STATE_CLEANING,
    "InDustCollecting": STATE_DOCKED,
    "standBy": STATE_IDLE,
    "explore": STATE_CLEANING,
    "cleanAll": STATE_CLEANING,
    "cleanArea": STATE_CLEANING,
    "cleanRoom": STATE_CLEANING,
    "fillWater": STATE_CLEANING,
    "deepWashing": STATE_CLEANING,
    "backToCharge": STATE_RETURNING,
    "markingWaterBase": STATE_CLEANING,
    "drying": STATE_CLEANING,
    "collectDust": STATE_CLEANING,
    "remoteControl": STATE_CLEANING,
    "cleanWithExplorer": STATE_CLEANING,
    "fillWaterForHumi": STATE_CLEANING,
    "markingHumi": STATE_CLEANING,
}

VACUUM_FAN_SPEED_TO_SWITCHBOT_FAN_SPEED: dict[str, int] = {
    VACUUM_FAN_SPEED_QUIET: 1,
    VACUUM_FAN_SPEED_STANDARD: 2,
    VACUUM_FAN_SPEED_STRONG: 3,
    VACUUM_FAN_SPEED_MAX: 4,
}

ATTR_WATER_BASE_BATTERY = "water_base_battery"

# https://github.com/OpenWonderLabs/SwitchBotAPI?tab=readme-ov-file#robot-vacuum-cleaner-s1-plus-1
class SwitchBotCloudVacuum(SwitchBotCloudEntity, StateVacuumEntity):
    """Representation of a SwitchBot vacuum."""

    _attr_supported_features: VacuumEntityFeature = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.CLEAN_SPOT
    )

    _attr_name = None

    _attr_fan_speed_list: list[str] = ClassVar[list](
        VACUUM_FAN_SPEED_TO_SWITCHBOT_FAN_SPEED.keys(),
    )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the vacuum cleaner."""
        data: dict[str, Any] = {}

        if self._water_base_battery is not None:
            data[ATTR_WATER_BASE_BATTERY] = self._water_base_battery

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        self._attr_fan_speed = fan_speed
        if fan_speed in VACUUM_FAN_SPEED_TO_SWITCHBOT_FAN_SPEED:
            await self.send_api_command(
                "changeParam",
                parameters={
                    "fanLevel": VACUUM_FAN_SPEED_TO_SWITCHBOT_FAN_SPEED[fan_speed],
                    "waterLevel": 1,
                    "times": 1,
                },
            )
        self.async_write_ha_state()

    async def async_pause(self) -> None:
        """Pause the cleaning task."""
        await self.send_api_command("pause")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self.send_api_command(VacuumCommands.DOCK)

    async def async_start(self) -> None:
        """Start or resume the cleaning task."""
        await self.send_api_command(
            "startClean",
            parameters={
                "action": "sweep",
                "param": {
                    "fanLevel": VACUUM_FAN_SPEED_TO_SWITCHBOT_FAN_SPEED[self._attr_fan_speed],
                    "waterLevel": 1,
                    "times": 1,
                },
            },
        )

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner.

        This method must be run in the event loop.
        """
        await self.send_api_command(
            command,
            parameters=params,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        self._attr_battery_level = self.coordinator.data.get("battery")
        self._attr_available = self.coordinator.data.get("onlineStatus") == "online"

        switchbot_state = str(self.coordinator.data.get("workingStatus"))
        self._attr_state = VACUUM_SWITCHBOT_STATE_TO_HA_STATE.get(switchbot_state)

        self.async_write_ha_state()


@callback
def _async_make_entity(
    api: SwitchBotAPI, device: Device | Remote, coordinator: SwitchBotCoordinator
) -> SwitchBotCloudVacuum:
    """Make a SwitchBotCloudVacuum."""
    return SwitchBotCloudVacuum(api, device, coordinator)
