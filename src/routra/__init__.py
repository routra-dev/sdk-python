"""
Routra Python SDK

Thin wrapper over the OpenAI Python SDK.
Adds typed routing metadata, policy helpers, and management namespaces.

Usage:
    from routra import Routra

    client = Routra(api_key="rtr-...", policy="cheapest")
    resp = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(resp.routra.provider, resp.routra.score)
"""

from routra._client import Routra, AsyncRoutra
from routra._types import RoutingMetadata
from routra.management import ManagementClient

__all__ = ["Routra", "AsyncRoutra", "RoutingMetadata", "ManagementClient"]
__version__ = "0.1.0"
