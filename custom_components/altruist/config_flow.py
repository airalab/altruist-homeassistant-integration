"""Config flow for the Altruist Sensor integration."""

import ipaddress
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ModuleNotFoundError:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .altruist_sensor import AltruistClient, AltruistDeviceModel, AltruistError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class AltruistConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Altruist Sensor."""

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.device: AltruistDeviceModel = None
        super().__init__()

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        ip_address = None
        if user_input is not None:
            ip_address = user_input.get("ip_address")
            if self._is_valid_ip(ip_address):
                try:
                    session = async_get_clientsession(self.hass)
                    client = await AltruistClient.from_ip_address(session, ip_address)
                except AltruistError:
                    errors["base"] = "no_device_found"
                else:
                    await self.async_set_unique_id(client.device_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=ip_address, data={"ip_address": ip_address, "id": client.device_id})
            else:
                errors["base"] = "invalid_ip"

        data_schema = vol.Schema({
            vol.Required("ip_address"): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors, description_placeholders={
                "ip_address": ip_address,
            },
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.info("Zeroconf discovery: %s", discovery_info)
        self.device = AltruistDeviceModel.from_zeroconf_service_info(discovery_info)
        _LOGGER.info("Zeroconf device: %s", self.device)
        await self.async_set_unique_id(self.device.id)
        self._abort_if_unique_id_configured()
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"{self.device.name} {self.device.id}",
                data={"ip_address": self.device.ip_address, "id": self.device.id},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "model": f"{self.device.name} {self.device.id}",
            },
        )

    def _is_valid_ip(self, ip_address: str) -> bool:
        """Validate the IP address."""
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return False
        else:
            return True
