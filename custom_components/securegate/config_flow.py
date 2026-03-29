"""Config flow for SecureGate."""
import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_NAME, CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_NAME, DEFAULT_SCAN_INTERVAL


async def validate_connection(host: str, port: int) -> dict:
    """Test connection to SecureGate."""
    try:
        async with async_timeout.timeout(5):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{host}:{port}/json") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"ok": True, "msg": data.get("system_msg", "Connected")}
                    return {"ok": False, "msg": f"HTTP {resp.status}"}
    except Exception as err:
        return {"ok": False, "msg": str(err)}


class SecureGateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SecureGate."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            result = await validate_connection(user_input[CONF_HOST], user_input.get(CONF_PORT, DEFAULT_PORT))
            if result["ok"]:
                await self.async_set_unique_id(f"securegate_{user_input[CONF_HOST]}_{user_input.get(CONF_PORT, DEFAULT_PORT)}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.135"): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
            errors=errors,
        )
