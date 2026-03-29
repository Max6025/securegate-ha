"""Shared helpers for SecureGate entities."""
from .const import DOMAIN


def device_room(coordinator, port, name):
    return {
        "identifiers": {(DOMAIN, f"{coordinator.host}:{port}")},
        "name": f"SecureGate — {name}",
        "manufacturer": "SecureGate",
        "model": "NFC Room Controller",
        "sw_version": "3.0",
        "via_device": (DOMAIN, f"{coordinator.host}_admin"),
    }


def device_admin(coordinator):
    return {
        "identifiers": {(DOMAIN, f"{coordinator.host}_admin")},
        "name": "SecureGate Admin",
        "manufacturer": "SecureGate",
        "model": "Admin Panel",
        "sw_version": "3.0",
        "configuration_url": f"http://{coordinator.host}/admin/",
    }
