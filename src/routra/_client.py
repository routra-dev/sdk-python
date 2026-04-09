"""
Routra client - subclasses openai.OpenAI.
Adds:
  - Typed .routra on completion responses
  - .policy() helper to set X-Routra-Policy header
"""
from __future__ import annotations

import functools
import os
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

        # Wrap chat.completions.create to inject typed .routra field (non-streaming)
        _orig = self.chat.completions.create

        @functools.wraps(_orig)
        async def _wrapped(*args, **kwargs):
            resp = await _orig(*args, **kwargs)
            stream = kwargs.get("stream", False)
            if not stream:
                _inject_routra(resp)
            return resp

        self.chat.completions.create = _wrapped  # type: ignore[method-assign]

    def with_policy(self, policy: str) -> "AsyncRoutra":
        """Return a copy of this client with the given policy set."""
        return AsyncRoutra(
            api_key=self.api_key,
            policy=policy,
            base_url=str(self.base_url),
        )
