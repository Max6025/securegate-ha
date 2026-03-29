"""Config flow for SecureGate."""
import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL, DEFAULT_NAME, DEFAULT_SCAN_INTERVAL


async def discover_rooms(host: str) -> list[dict]:
    """Discover SecureGate rooms by scanning ports."""
    rooms = []
    ports = [5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800, 5900]
    try:
        async with async_timeout.timeout(12):
            async with aiohttp.ClientSession() as session:
                for port in ports:
                    try:
                        async with session.get(
                            f"http://{host}:{port}/api/config",
                            timeout=aiohttp.ClientTimeout(total=2)
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                name = data.get("room_name", data.get("title", f"Raum {port}"))
                                rooms.append({"name": name, "port": port})
                    except Exception:
                        continue
    except Exception:
        pass
    # Fallback
    if not rooms:
        try:
            async with async_timeout.timeout(3):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{host}:5000/json", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        if resp.status == 200:
                            rooms.append({"name": "SecureGate", "port": 5000})
        except Exception:
            pass
    return rooms


class SecureGateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            rooms = await discover_rooms(host)
            if rooms:
                await self.async_set_unique_id(f"securegate_{host}")
                self._abort_if_unique_id_configured()
                room_names = ", ".join(r["name"] for r in rooms)
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={**user_input, "rooms": rooms},
                    description_placeholders={"rooms": room_names},
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.135"): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
            errors=errors,
        )
