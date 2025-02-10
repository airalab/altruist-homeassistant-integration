from copy import deepcopy
import json
import logging

from aiohttp import ClientError, ClientSession
from aiohttp.client_exceptions import ClientConnectorError
import async_timeout

from .model import AltruistDeviceModel
from .errors import AltruistError

_LOGGER: logging.Logger = logging.getLogger(__name__)


class AltruistClient:
    """Class for handling the data retrieval."""

    def __init__(self, session: ClientSession, device: AltruistDeviceModel) -> None:
        """Initialize the data object."""
        self._session = session
        self._resource = f"http://{device.ip_address}/data.json"
        self.device = device
        self._last_data: list | None = None

    @classmethod
    async def from_ip_address(
        cls, session: ClientSession, ip_address: str
    ) -> "AltruistClient":
        """Create client from given IP address."""
        try:
            with async_timeout.timeout(30):
                response = await session.get(f"http://{ip_address}/data.json")
        except ClientConnectorError:
            _LOGGER.error("Can't connect to Altruist Sensor on %s", ip_address)
            raise AltruistError
        responseData = await response.text()
        _LOGGER.debug("Received data: %s", str(responseData))
        parsed_json = json.loads(responseData)
        if "software_version" in parsed_json:
            device = AltruistDeviceModel(
                id=parsed_json.get("sensor_id", ip_address),
                ip_address=ip_address,
                fw_version=parsed_json["software_version"],
            )
            return cls(session, device)
        raise AltruistError

    @property
    def fw_version(self) -> str | None:
        """The firmware version of the sensor."""
        return self.device.fw_version

    @property
    def device_id(self) -> str:
        """The mac address of the sensor."""
        return self.device.id

    @property
    def sensor_names(self) -> list[str]:
        """Get the list of the sensor measurements names."""
        if self._last_data:
            return [
                item["value_type"]
                for item in self._last_data
                if self._valid_sensor_name(item["value_type"])
            ]
        return []

    def _valid_sensor_name(self, sensor_name: str) -> bool:
        """Return True if the sensor name is supported."""
        if "GPS" in sensor_name:
            return False
        if "samples" in sensor_name:
            return False
        if "micro" in sensor_name:
            return False
        if "interval" in sensor_name:
            return False
        return True

    async def fetch_data(self) -> dict:
        """Get the latest data from Luftdaten service."""
        responseData = None
        try:
            _LOGGER.debug("Get data from %s", str(self._resource))
            with async_timeout.timeout(30):
                response = await self._session.get(self._resource)
            responseData = await response.text()
            _LOGGER.debug("Received data: %s", str(responseData))
        except ClientError as err:
            _LOGGER.warning("REST request error: %s", err)
            raise AltruistError from err
        except TimeoutError:
            _LOGGER.warning("REST request timeout")
            raise AltruistError from TimeoutError

        try:
            parsed_json = json.loads(responseData)
            if not isinstance(parsed_json, dict):
                _LOGGER.warning("JSON result was not a dictionary")
                parsed_json = {}
            self.device.fw_version = parsed_json.get("software_version")
            data = parsed_json.get("sensordatavalues", {})
        except ValueError:
            _LOGGER.warning("REST result could not be parsed as JSON")
            raise AltruistError from ValueError
        self._last_data = deepcopy(data)
        return data
