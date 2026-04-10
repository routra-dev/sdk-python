"""
Routra Management API client.

Provides typed access to all Routra management endpoints:
keys, policies, usage, billing, batch, webhooks, BYOK, notifications, providers.

Uses httpx under the hood (bundled with openai).

Example:
    from routra import Routra

    client = Routra(api_key="rtr-...")
    keys = client.management.keys.list()
    usage = client.management.usage.get()
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# ── Types ──────────────────────────────────────────────────────────────────────

@dataclass
class KeySummary:
    id: str
    name: str
    prefix: str
    created_at: str
    last_used_at: Optional[str] = None
    policy_id: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    rate_limit_rpd: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict) -> KeySummary:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class CreateKeyRequest:
    name: str
    policy_id: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    rate_limit_rpd: Optional[int] = None


@dataclass
class CreateKeyResponse:
    id: str
    key: str
    prefix: str
    name: str

    @classmethod
    def from_dict(cls, d: dict) -> CreateKeyResponse:
        return cls(**{k: d[k] for k in cls.__dataclass_fields__})


@dataclass
class PolicyResponse:
    id: str
    name: str
    strategy: str
    constraints: dict
    created_at: str

    @classmethod
    def from_dict(cls, d: dict) -> PolicyResponse:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class CreatePolicyRequest:
    name: str
    strategy: str
    constraints: Optional[dict] = None


@dataclass
class ModalityUsage:
    usage_unit: str
    request_count: int
    total_cost_usd: float
    total_usage_value: float

    @classmethod
    def from_dict(cls, d: dict) -> ModalityUsage:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class UsageSummary:
    total_requests: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    period_start: str
    period_end: str
    modality_breakdown: list[ModalityUsage] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> UsageSummary:
        mods = [ModalityUsage.from_dict(m) for m in d.get("modality_breakdown", [])]
        return cls(
            total_requests=d.get("total_requests", 0),
            total_cost_usd=d.get("total_cost_usd", 0.0),
            total_input_tokens=d.get("total_input_tokens", 0),
            total_output_tokens=d.get("total_output_tokens", 0),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            modality_breakdown=mods,
        )


@dataclass
class CostBreakdownItem:
    model: str
    provider: str
    request_count: int
    total_cost_usd: float
    input_tokens: int
    output_tokens: int

    @classmethod
    def from_dict(cls, d: dict) -> CostBreakdownItem:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class RequestLogEntry:
    id: str
    model: str
    provider: str
    latency_ms: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    created_at: str
    usage_unit: Optional[str] = None
    usage_value: Optional[float] = None

    @classmethod
    def from_dict(cls, d: dict) -> RequestLogEntry:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class BillingInfo:
    billing_tier: str
    credit_balance_usd: float
    monthly_spend_usd: float
    subscription_status: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> BillingInfo:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class CreateCheckoutRequest:
    plan: str


@dataclass
class CreateCheckoutResponse:
    checkout_url: str

    @classmethod
    def from_dict(cls, d: dict) -> CreateCheckoutResponse:
        return cls(checkout_url=d["checkout_url"])


@dataclass
class TopupRequest:
    amount_usd: float


@dataclass
class BatchJobResponse:
    id: str
    status: str
    total_requests: int
    completed_requests: int
    failed_requests: int
    created_at: str

    @classmethod
    def from_dict(cls, d: dict) -> BatchJobResponse:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class CreateBatchRequest:
    requests: list[dict]
    policy: Optional[str] = None


@dataclass
class WebhookEndpointResponse:
    id: str
    url: str
    events: list[str]
    active: bool
    created_at: str

    @classmethod
    def from_dict(cls, d: dict) -> WebhookEndpointResponse:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class CreateWebhookRequest:
    url: str
    events: list[str]


@dataclass
class StoreKeyRequest:
    api_key: str


@dataclass
class NotificationPreferenceResponse:
    event_type: str
    email_enabled: bool
    webhook_enabled: bool
    in_app_enabled: bool

    @classmethod
    def from_dict(cls, d: dict) -> NotificationPreferenceResponse:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class InboxItemResponse:
    id: str
    event_type: str
    title: str
    body: str
    read: bool
    created_at: str

    @classmethod
    def from_dict(cls, d: dict) -> InboxItemResponse:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class ProviderInfo:
    slug: str
    name: str
    is_healthy: bool
    supported_modalities: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> ProviderInfo:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class AuditLogEntry:
    id: str
    action: str
    actor: str
    resource_type: str
    resource_id: str
    created_at: str
    details: Optional[dict] = None

    @classmethod
    def from_dict(cls, d: dict) -> AuditLogEntry:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


# ── HTTP helper ────────────────────────────────────────────────────────────────

class _APIError(Exception):
    """Raised when the Routra management API returns a non-2xx status."""
    def __init__(self, status: int, body: str, method: str, path: str):
        self.status = status
        self.body = body
        super().__init__(f"Routra API {method} {path} failed ({status}): {body}")


def _request(base_url: str, api_key: str, method: str, path: str, body: Any = None) -> Any:
    url = f"{base_url}/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as resp:  # noqa: S310
            if resp.status == 204:
                return None
            return json.loads(resp.read())
    except HTTPError as e:
        raise _APIError(e.code, e.read().decode(errors="replace"), method, path) from None


# ── Resource namespaces ────────────────────────────────────────────────────────

class _KeysResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def create(self, *, name: str, policy_id: str | None = None,
               rate_limit_rpm: int | None = None, rate_limit_rpd: int | None = None) -> CreateKeyResponse:
        body: dict[str, Any] = {"name": name}
        if policy_id is not None:
            body["policy_id"] = policy_id
        if rate_limit_rpm is not None:
            body["rate_limit_rpm"] = rate_limit_rpm
        if rate_limit_rpd is not None:
            body["rate_limit_rpd"] = rate_limit_rpd
        return CreateKeyResponse.from_dict(_request(self._base, self._key, "POST", "/keys", body))

    def list(self) -> list[KeySummary]:
        return [KeySummary.from_dict(k) for k in _request(self._base, self._key, "GET", "/keys")]

    def revoke(self, key_id: str) -> None:
        _request(self._base, self._key, "DELETE", f"/keys/{key_id}")

    def rotate(self, key_id: str) -> CreateKeyResponse:
        return CreateKeyResponse.from_dict(_request(self._base, self._key, "POST", f"/keys/{key_id}/rotate"))


class _PoliciesResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def create(self, *, name: str, strategy: str, constraints: dict | None = None) -> PolicyResponse:
        body: dict[str, Any] = {"name": name, "strategy": strategy}
        if constraints is not None:
            body["constraints"] = constraints
        return PolicyResponse.from_dict(_request(self._base, self._key, "POST", "/policies", body))

    def list(self) -> list[PolicyResponse]:
        return [PolicyResponse.from_dict(p) for p in _request(self._base, self._key, "GET", "/policies")]


class _UsageResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def get(self) -> UsageSummary:
        return UsageSummary.from_dict(_request(self._base, self._key, "GET", "/usage"))

    def cost_breakdown(self) -> list[CostBreakdownItem]:
        return [CostBreakdownItem.from_dict(i) for i in _request(self._base, self._key, "GET", "/usage/cost-breakdown")]

    def requests(self, *, limit: int = 50, offset: int = 0) -> list[RequestLogEntry]:
        return [RequestLogEntry.from_dict(r) for r in _request(self._base, self._key, "GET", f"/requests?limit={limit}&offset={offset}")]


class _BillingResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def get(self) -> BillingInfo:
        return BillingInfo.from_dict(_request(self._base, self._key, "GET", "/billing"))

    def create_checkout(self, *, plan: str) -> CreateCheckoutResponse:
        return CreateCheckoutResponse.from_dict(_request(self._base, self._key, "POST", "/billing/checkout", {"plan": plan}))

    def cancel_subscription(self) -> None:
        _request(self._base, self._key, "DELETE", "/billing/subscription")

    def topup(self, *, amount_usd: float) -> CreateCheckoutResponse:
        return CreateCheckoutResponse.from_dict(_request(self._base, self._key, "POST", "/billing/topup", {"amount_usd": amount_usd}))


class _BatchResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def create(self, *, requests: list[dict], policy: str | None = None) -> BatchJobResponse:
        body: dict[str, Any] = {"requests": requests}
        if policy is not None:
            body["policy"] = policy
        return BatchJobResponse.from_dict(_request(self._base, self._key, "POST", "/batch", body))

    def list(self) -> list[BatchJobResponse]:
        return [BatchJobResponse.from_dict(j) for j in _request(self._base, self._key, "GET", "/batch")]

    def status(self, job_id: str) -> BatchJobResponse:
        return BatchJobResponse.from_dict(_request(self._base, self._key, "GET", f"/batch/{job_id}/status"))

    def results(self, job_id: str) -> Any:
        return _request(self._base, self._key, "GET", f"/batch/{job_id}/results")

    def cancel(self, job_id: str) -> None:
        _request(self._base, self._key, "POST", f"/batch/{job_id}/cancel")


class _WebhooksResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def create(self, *, url: str, events: list[str]) -> WebhookEndpointResponse:
        return WebhookEndpointResponse.from_dict(_request(self._base, self._key, "POST", "/webhooks", {"url": url, "events": events}))

    def list(self) -> list[WebhookEndpointResponse]:
        return [WebhookEndpointResponse.from_dict(w) for w in _request(self._base, self._key, "GET", "/webhooks")]

    def delete(self, webhook_id: str) -> None:
        _request(self._base, self._key, "DELETE", f"/webhooks/{webhook_id}")


class _ProviderKeysResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def store(self, provider_slug: str, *, api_key: str) -> None:
        _request(self._base, self._key, "POST", f"/provider-keys/{provider_slug}", {"api_key": api_key})

    def list(self) -> list[dict]:
        return _request(self._base, self._key, "GET", "/provider-keys")

    def delete(self, provider_slug: str) -> None:
        _request(self._base, self._key, "DELETE", f"/provider-keys/{provider_slug}")

    def verify(self, provider_slug: str) -> dict:
        return _request(self._base, self._key, "POST", f"/provider-keys/{provider_slug}/verify")


class _NotificationsResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def list_preferences(self) -> list[NotificationPreferenceResponse]:
        return [NotificationPreferenceResponse.from_dict(p) for p in _request(self._base, self._key, "GET", "/notifications/preferences")]

    def update_preference(self, event_type: str, *, email_enabled: bool | None = None,
                          webhook_enabled: bool | None = None, in_app_enabled: bool | None = None) -> None:
        body: dict[str, Any] = {"event_type": event_type}
        if email_enabled is not None:
            body["email_enabled"] = email_enabled
        if webhook_enabled is not None:
            body["webhook_enabled"] = webhook_enabled
        if in_app_enabled is not None:
            body["in_app_enabled"] = in_app_enabled
        _request(self._base, self._key, "PUT", "/notifications/preferences", body)

    def list_inbox(self, *, limit: int = 20, offset: int = 0) -> list[InboxItemResponse]:
        return [InboxItemResponse.from_dict(i) for i in _request(self._base, self._key, "GET", f"/notifications/inbox?limit={limit}&offset={offset}")]

    def mark_read(self, notification_id: str) -> None:
        _request(self._base, self._key, "POST", f"/notifications/inbox/{notification_id}/read")

    def mark_all_read(self) -> None:
        _request(self._base, self._key, "POST", "/notifications/inbox/read-all")

    def unread_count(self) -> int:
        return _request(self._base, self._key, "GET", "/notifications/inbox/unread-count")["count"]


class _ProvidersResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def list(self) -> list[ProviderInfo]:
        data = _request(self._base, self._key, "GET", "/providers")
        return [ProviderInfo.from_dict(p) for p in data.get("providers", data)]

    def catalog(self) -> Any:
        return _request(self._base, self._key, "GET", "/models/catalog")


class _AuditLogResource:
    def __init__(self, base_url: str, api_key: str):
        self._base = base_url
        self._key = api_key

    def list(self, *, limit: int = 50, offset: int = 0) -> list[AuditLogEntry]:
        return [AuditLogEntry.from_dict(e) for e in _request(self._base, self._key, "GET", f"/audit-log?limit={limit}&offset={offset}")]


# ── Main Management Client ─────────────────────────────────────────────────────

class ManagementClient:
    """
    Routra Management API client.

    Access via ``client.management`` on a :class:`~routra.Routra` instance,
    or instantiate directly::

        from routra.management import ManagementClient
        mgmt = ManagementClient(base_url="https://api.routra.dev", api_key="rtr-...")
    """

    def __init__(self, base_url: str, api_key: str):
        self._base = base_url.rstrip("/")
        self._key = api_key

        self.keys = _KeysResource(self._base, self._key)
        self.policies = _PoliciesResource(self._base, self._key)
        self.usage = _UsageResource(self._base, self._key)
        self.billing = _BillingResource(self._base, self._key)
        self.batch = _BatchResource(self._base, self._key)
        self.webhooks = _WebhooksResource(self._base, self._key)
        self.provider_keys = _ProviderKeysResource(self._base, self._key)
        self.notifications = _NotificationsResource(self._base, self._key)
        self.providers = _ProvidersResource(self._base, self._key)
        self.audit_log = _AuditLogResource(self._base, self._key)
