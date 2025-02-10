"""Module for Altruist device model."""

from dataclasses import dataclass

from zeroconf.asyncio import AsyncServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo


@dataclass
class AltruistDeviceModel:
    """Data class for storing information about an Altruist device."""

    id: str
    ip_address: str
    name: str = "Altruist Sensor"
    fw_version: str | None = None

    @classmethod
    def from_zeroconf_service_info(cls, info: ZeroconfServiceInfo) -> "AltruistDeviceModel":
        """Create an AltruistDevice instance from an AsyncServiceInfo.

        This method extracts the device id and ip address from the AsyncServiceInfo.
        Adjust the parsing logic as required.
        """
        device_id = info.name.split(".")[0].split("-")[-1]
        ip_address = str(info.ip_address)
        return cls(id=device_id, ip_address=ip_address)

    @classmethod
    def from_async_service_info(cls, info: AsyncServiceInfo) -> "AltruistDeviceModel":
        """Create an AltruistDevice instance from an AsyncServiceInfo.

        This method extracts the device id and ip address from the AsyncServiceInfo.
        Adjust the parsing logic as required.
        """
        device_id = info.name.split(".")[0].split("-")[-1]
        ip_address = info.parsed_addresses()[0]
        return cls(id=device_id, ip_address=ip_address)