"""
Routra client — subclasses openai.OpenAI.
Adds:
  - Typed .routra on completion responses
  - .policy() helper to set X-Routra-Policy header
  - .batch, .usage, .policies namespaces (TODO Phase 4: generated from OpenAPI spec)
"""
from __future__ import annotations

from typing import Optional
import openai

BASE_URL = "https://api.routra.dev/v1"


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
