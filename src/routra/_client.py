"""
Routra client - subclasses openai.OpenAI.
Adds:
  - Typed .routra on completion/image/embedding/audio responses
  - .policy() helper to set X-Routra-Policy header
"""
from __future__ import annotations

import functools
import os
from typing import Optional, Any
import openai

from routra._types import RoutingMetadata
from routra.management import ManagementClient

BASE_URL = "https://api.routra.dev/v1"


def _inject_routra(resp: Any) -> Any:
    """Attach a typed .routra attribute to any response with model_extra."""
    raw = (getattr(resp, "model_extra", None) or {}).get("routra")
    if raw and isinstance(raw, dict):
        object.__setattr__(resp, "routra", RoutingMetadata.from_dict(raw))
    else:
        object.__setattr__(resp, "routra", None)
    return resp


def _wrap_sync(original):
    """Wrap a sync SDK method to inject .routra metadata on non-streaming responses."""
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        resp = original(*args, **kwargs)
        stream = kwargs.get("stream", False)
        if not stream:
            _inject_routra(resp)
        return resp
    return wrapper


def _wrap_async(original):
    """Wrap an async SDK method to inject .routra metadata on non-streaming responses."""
    @functools.wraps(original)
    async def wrapper(*args, **kwargs):
        resp = await original(*args, **kwargs)
        stream = kwargs.get("stream", False)
        if not stream:
            _inject_routra(resp)
        return resp
    return wrapper


class Routra(openai.OpenAI):
    """
    Routra client. Drop-in replacement for openai.OpenAI.

    Args:
        api_key:  Routra API key (rtr-...). Falls back to ROUTRA_API_KEY env var.
        policy:   Default routing policy name (sets X-Routra-Policy header)
        base_url: Override API base URL. Falls back to ROUTRA_BASE_URL env var.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        policy: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        resolved_key = api_key or os.environ.get("ROUTRA_API_KEY")
        if not resolved_key:
            raise ValueError(
                "No API key provided. Pass api_key= or set ROUTRA_API_KEY env var."
            )

        resolved_url = base_url or os.environ.get("ROUTRA_BASE_URL", BASE_URL)

        headers = kwargs.pop("default_headers", {})
        if policy:
            headers["X-Routra-Policy"] = policy

        super().__init__(
            api_key=resolved_key,
            base_url=resolved_url,
            default_headers=headers,
            **kwargs,
        )
        self._routra_policy = policy

        # Wrap all proxy endpoints to inject typed .routra metadata
        self.chat.completions.create = _wrap_sync(self.chat.completions.create)  # type: ignore[method-assign]
        self.embeddings.create = _wrap_sync(self.embeddings.create)  # type: ignore[method-assign]
        self.images.generate = _wrap_sync(self.images.generate)  # type: ignore[method-assign]
        self.audio.transcriptions.create = _wrap_sync(self.audio.transcriptions.create)  # type: ignore[method-assign]

        # Management API client
        mgmt_base = resolved_url.rstrip("/").removesuffix("/v1")
        self.management = ManagementClient(mgmt_base, resolved_key)

    def with_policy(self, policy: str) -> "Routra":
        """Return a copy of this client with the given policy set."""
        return Routra(
            api_key=self.api_key,
            policy=policy,
            base_url=str(self.base_url),
        )


class AsyncRoutra(openai.AsyncOpenAI):
    """Async version of the Routra client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        policy: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        resolved_key = api_key or os.environ.get("ROUTRA_API_KEY")
        if not resolved_key:
            raise ValueError(
                "No API key provided. Pass api_key= or set ROUTRA_API_KEY env var."
            )

        resolved_url = base_url or os.environ.get("ROUTRA_BASE_URL", BASE_URL)

        headers = kwargs.pop("default_headers", {})
        if policy:
            headers["X-Routra-Policy"] = policy

        super().__init__(
            api_key=resolved_key,
            base_url=resolved_url,
            default_headers=headers,
            **kwargs,
        )
        self._routra_policy = policy

        # Wrap all proxy endpoints to inject typed .routra metadata
        self.chat.completions.create = _wrap_async(self.chat.completions.create)  # type: ignore[method-assign]
        self.embeddings.create = _wrap_async(self.embeddings.create)  # type: ignore[method-assign]
        self.images.generate = _wrap_async(self.images.generate)  # type: ignore[method-assign]
        self.audio.transcriptions.create = _wrap_async(self.audio.transcriptions.create)  # type: ignore[method-assign]

        # Management API client (sync — async users can wrap or use httpx directly)
        mgmt_base = resolved_url.rstrip("/").removesuffix("/v1")
        self.management = ManagementClient(mgmt_base, resolved_key)

    def with_policy(self, policy: str) -> "AsyncRoutra":
        """Return a copy of this client with the given policy set."""
        return AsyncRoutra(
            api_key=self.api_key,
            policy=policy,
            base_url=str(self.base_url),
        )
