from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingMetadata:
    """Routing metadata returned by Routra on every non-streaming completion response."""

    provider: str
    latency_ms: int
    score: float
    cost_usd: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    failover: Optional[bool] = None
    ttfb_ms: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict) -> "RoutingMetadata":
        return cls(
            provider=d.get("provider", ""),
            latency_ms=d.get("latency_ms", 0),
            score=d.get("score", 0.0),
            cost_usd=d.get("cost_usd"),
            input_tokens=d.get("input_tokens"),
            output_tokens=d.get("output_tokens"),
            failover=d.get("failover"),
            ttfb_ms=d.get("ttfb_ms"),
        )
