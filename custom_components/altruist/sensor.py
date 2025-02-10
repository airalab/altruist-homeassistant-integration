from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .altruist_sensor import AltruistClient, AltruistDeviceModel
from .const import SENSOR_DESCRIPTIONS, DOMAIN
from . import AltruistConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AltruistConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    client = config_entry.runtime_data
    coordinator = AltruistDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    sensors = [AltruistSensor(coordinator, client.device, SENSOR_DESCRIPTIONS[sensor_name]) for sensor_name in client.sensor_names]
    async_add_entities(sensors)


class AltruistDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: AltruistClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Altruist",
            update_interval=timedelta(seconds=15),
        )
        self._client = client

    async def _async_update_data(self) -> dict:
        return await self._client.fetch_data()


class AltruistSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a LuftdatenSensor sensor."""

    _name: str
    _native_value: Any

    def __init__(self, coordinator: DataUpdateCoordinator, device: AltruistDeviceModel, description: SensorEntityDescription) -> None:
        """Initialize the LuftdatenSensor sensor."""
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.id
        self._name = f"altruist_{device.id}"
        self._native_value = None
        self.entity_description = description

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f'{self._name}-{self.entity_description.key}'

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f'{self._name} {self.entity_description.name}'

    @property
    def native_value(self) -> float | int:
        """Return the value reported by the sensor."""
        return self._native_value

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        if self.device_class in [SensorDeviceClass.PM1, SensorDeviceClass.PM25]:
            return 'mdi:thought-bubble-outline'
        if self.device_class == SensorDeviceClass.PM10:
            return 'mdi:thought-bubble'

        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._name)
            },
            name=f"Altruist Sensor {self._device_id}",
            manufacturer="Robonomics",
            model="Altruist Sensor",
            sw_version=self._device.fw_version,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for sensordata_value in self.coordinator.data:
            if sensordata_value['value_type'] == self.entity_description.key:
                self._native_value = float(sensordata_value['value']) if "." in sensordata_value['value'] else int(sensordata_value['value'])
        self.async_write_ha_state()
