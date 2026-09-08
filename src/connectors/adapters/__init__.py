from __future__ import annotations

from typing import Any, Protocol

from src.connectors.adapters.base_adapter import BaseAdapter
from src.connectors.adapters.email_adapter import EmailAdapter
from src.connectors.adapters.linkedin_adapter import LinkedInAdapter
from src.connectors.adapters.media_adapter import MediaAdapter

_ADAPTER_REGISTRY: dict[str, BaseAdapter] = {}

def register_adapter(channel: str, adapter: BaseAdapter) -> None:
    _ADAPTER_REGISTRY[channel.lower()] = adapter

def get_adapter(channel: str) -> BaseAdapter | None:
    return _ADAPTER_REGISTRY.get(channel.lower())

def _init_adapters() -> None:
    register_adapter("email", EmailAdapter())
    register_adapter("linkedin", LinkedInAdapter())
    register_adapter("media_ads", MediaAdapter())
    register_adapter("inbound", MediaAdapter())

_init_adapters()
