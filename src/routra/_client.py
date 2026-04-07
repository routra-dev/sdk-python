"""
Routra client - subclasses openai.OpenAI.
Adds:
  - Typed .routra on completion responses
  - .policy() helper to set X-Routra-Policy header
  - .batch, .usage, .policies namespaces (TODO Phase 4: generated from OpenAPI spec)
"""
from __future__ import annotations

import functools
from typing import Optional, Any
import openai

from routra._types import RoutingMetadata

BASE_URL = "https://api.routra.dev/v1"


def _inject_routra(resp: Any) -> Any:
    """Attach a typed .routra attribute to a ChatCompletion response."""
    raw = (getattr(resp, "model_extra", None) or {}).get("routra")
    if raw and isinstance(raw, dict):
        object.__setattr__(resp, "routra", RoutingMetadata.from_dict(raw))
    else:
        object.__setattr__(resp, "routra", None)
    return resp


class Routra(openai.OpenAI):
    """
    Routra client. Drop-in replacement for openai.OpenAI.

    Args:
        api_key:  Routra API key (rtr-...)
        policy:   Default routing policy name (sets X-Routra-Policy header)
        base_url: Override API base URL (useful for local dev)
    """

    def __init__(
        self,
        api_key: str,
        policy: Optional[str] = None,
        base_url: str = BASE_URL,
        **kwargs,
    ):
        headers = kwargs.pop("default_headers", {})
        if policy:
            headers["X-Routra-Policy"] = policy

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_headers=headers,
            **kwargs,
        )

        # Wrap chat.completions.create to inject typed .routra field (non-streaming)
        _orig = self.chat.completions.create

        @functools.wraps(_orig)
        def _wrapped(*args, **kwargs):
            resp = _orig(*args, **kwargs)
            stream = kwargs.get("stream", False)
            if not stream:
                _inject_routra(resp)
            return resp

        self.chat.completions.create = _wrapped  # type: ignore[method-assign]

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
        api_key: str,
        policy: Optional[str] = None,
        base_url: str = BASE_URL,
        **kwargs,
    ):
        headers = kwargs.pop("default_headers", {})
        if policy:
            headers["X-Routra-Policy"] = policy

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_headers=headers,
            **kwargs,
        )

        # Wrap async chat.completions.create to inject typed .routra field
        _orig = self.chat.completions.create

        @functools.wraps(_orig)
        async def _wrapped_async(*args, **kwargs):
            resp = await _orig(*args, **kwargs)
            stream = kwargs.get("stream", False)
            if not stream:
                _inject_routra(resp)
            return resp

        self.chat.completions.create = _wrapped_async  # type: ignore[method-assign]

    def with_policy(self, policy: str) -> "AsyncRoutra":
        """Return a copy of this client with the given policy set."""
        return AsyncRoutra(
            api_key=self.api_key,
            policy=policy,
            base_url=str(self.base_url),
        )
