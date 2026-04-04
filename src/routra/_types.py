from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingMetadata:
    """Routing metadata returned by Routra on every completion response."""
    provider: str
    latency_ms: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    score_selected: float
    failover: bool
    ttfb_ms: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict) -> "RoutingMetadata":
        return cls(
            provider=d.get("provider", ""),
            latency_ms=d.get("latency_ms", 0),
            cost_usd=d.get("cost_usd", 0.0),
            input_tokens=d.get("input_tokens", 0),
            output_tokens=d.get("output_tokens", 0),
            score_selected=d.get("score_selected", 0.0),
            failover=d.get("failover", False),
            ttfb_ms=d.get("ttfb_ms"),
        )
