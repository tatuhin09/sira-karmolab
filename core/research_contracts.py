"""Provider-neutral contracts for universal research execution."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


MAX_QUERY_CHARS = 4000
MAX_RESULTS = 20
MAX_PROVIDER_ATTEMPTS = 32
MAX_RECORDS = 200
MAX_FAILURE_TEXT = 500
MAX_RESOURCE_KEYS = 32
MAX_METADATA_JSON_CHARS = 8000


def _bounded_text(value: object, *, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    value = " ".join(value.split())
    if not value or len(value) > maximum:
        raise ValueError(f"{name} must contain 1..{maximum} characters")
    return value


def _nonnegative_int(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _validate_metadata(value: Mapping[str, Any]) -> None:
    if len(value) > MAX_RESOURCE_KEYS:
        raise ValueError("metadata is too large")
    for key in value:
        _bounded_text(key, name="metadata key", maximum=100)
    try:
        rendered = json.dumps(
            dict(value),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("metadata must contain finite JSON-compatible data") from exc
    if len(rendered) > MAX_METADATA_JSON_CHARS:
        raise ValueError("metadata exceeds bounded serialized size")


def _validate_failure(value: Mapping[str, Any]) -> dict[str, Any]:
    if len(value) > MAX_RESOURCE_KEYS:
        raise ValueError("failure contains too many entries")

    clean: dict[str, Any] = {}
    for key, item in value.items():
        key = _bounded_text(key, name="failure key", maximum=100)
        if key in clean:
            raise ValueError("failure contains duplicate normalized keys")

        if isinstance(item, str):
            item = _bounded_text(
                item, name=f"failure[{key}]", maximum=MAX_FAILURE_TEXT
            )
        elif item is None or isinstance(item, bool):
            pass
        elif type(item) is int:
            pass
        elif type(item) is float and math.isfinite(item):
            pass
        else:
            raise ValueError(
                f"failure[{key}] must be a bounded scalar value"
            )
        clean[key] = item
    return clean


def _validate_retry_after(value: object) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("retry_after must be numeric or null")
    if not math.isfinite(value) or value < 0:
        raise ValueError("retry_after must be finite and non-negative")
    return value


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """One bounded provider-independent research request."""

    query: str
    capability: str
    max_results: int = 3
    allow_metered: bool = False
    use_cache: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "query",
            _bounded_text(self.query, name="query", maximum=MAX_QUERY_CHARS),
        )
        object.__setattr__(
            self,
            "capability",
            _bounded_text(self.capability, name="capability", maximum=128),
        )
        if type(self.max_results) is not int or not 1 <= self.max_results <= MAX_RESULTS:
            raise ValueError(f"max_results must be 1..{MAX_RESULTS}")
        if not isinstance(self.allow_metered, bool):
            raise ValueError("allow_metered must be boolean")
        if not isinstance(self.use_cache, bool):
            raise ValueError("use_cache must be boolean")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        _validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "capability": self.capability,
            "max_results": self.max_results,
            "allow_metered": self.allow_metered,
            "use_cache": self.use_cache,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProviderExecutionResult:
    """Canonical result of one provider execution attempt."""

    status: str
    provider_id: str
    capability: str
    records: tuple[Any, ...] = ()
    api_requests: int = 0
    resource_usage: Mapping[str, int] = field(default_factory=dict)
    cache_hit: bool = False
    retryable: bool = False
    retry_after: float | None = None
    failure: Mapping[str, Any] | None = None
    providers_attempted: tuple[str, ...] = ()
    fallback_used: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"completed", "no_results", "failed", "cancelled"}:
            raise ValueError("invalid provider execution status")
        provider_id = _bounded_text(
            self.provider_id, name="provider_id", maximum=128
        )
        capability = _bounded_text(
            self.capability, name="capability", maximum=128
        )
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "capability", capability)

        if not isinstance(self.records, tuple):
            raise ValueError("records must be a tuple")
        if len(self.records) > MAX_RECORDS:
            raise ValueError("records exceed bounded execution limit")
        _nonnegative_int(self.api_requests, name="api_requests")

        if not isinstance(self.resource_usage, Mapping):
            raise ValueError("resource_usage must be a mapping")
        if len(self.resource_usage) > MAX_RESOURCE_KEYS:
            raise ValueError("resource_usage is too large")
        clean_usage: dict[str, int] = {}
        for key, value in self.resource_usage.items():
            key = _bounded_text(key, name="resource key", maximum=100)
            if key in clean_usage:
                raise ValueError("resource_usage contains duplicate normalized keys")
            clean_usage[key] = _nonnegative_int(
                value, name=f"resource_usage[{key}]"
            )
        object.__setattr__(self, "resource_usage", clean_usage)

        if not isinstance(self.cache_hit, bool):
            raise ValueError("cache_hit must be boolean")
        if not isinstance(self.retryable, bool):
            raise ValueError("retryable must be boolean")
        if self.retry_after is not None:
            _validate_retry_after(self.retry_after)
        if self.failure is not None:
            if not isinstance(self.failure, Mapping):
                raise ValueError("failure must be a mapping or null")
            object.__setattr__(self, "failure", _validate_failure(self.failure))
        if not isinstance(self.providers_attempted, tuple):
            raise ValueError("providers_attempted must be a tuple")
        if len(self.providers_attempted) > MAX_PROVIDER_ATTEMPTS:
            raise ValueError("providers_attempted exceeds bounded limit")
        clean_attempted = tuple(
            _bounded_text(item, name="attempted provider ID", maximum=128)
            for item in self.providers_attempted
        )
        object.__setattr__(self, "providers_attempted", clean_attempted)
        if not isinstance(self.fallback_used, bool):
            raise ValueError("fallback_used must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider_id": self.provider_id,
            "capability": self.capability,
            "records": list(self.records),
            "api_requests": self.api_requests,
            "resource_usage": dict(self.resource_usage),
            "cache_hit": self.cache_hit,
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "failure": dict(self.failure) if self.failure is not None else None,
            "providers_attempted": list(self.providers_attempted),
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True, slots=True)
class ResearchAttempt:
    """Audit-friendly summary of one provider attempt."""

    provider_id: str
    capability: str
    status: str
    api_requests: int = 0
    record_count: int = 0
    cache_hit: bool = False
    retryable: bool = False
    retry_after: float | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_id",
            _bounded_text(self.provider_id, name="provider_id", maximum=128),
        )
        object.__setattr__(
            self, "capability",
            _bounded_text(self.capability, name="capability", maximum=128),
        )
        if self.status not in {
            "completed", "partial", "no_results", "failed", "cancelled"
        }:
            raise ValueError("invalid research attempt status")
        _nonnegative_int(self.api_requests, name="api_requests")
        _nonnegative_int(self.record_count, name="record_count")
        if not isinstance(self.cache_hit, bool):
            raise ValueError("cache_hit must be boolean")
        if not isinstance(self.retryable, bool):
            raise ValueError("retryable must be boolean")
        if self.retry_after is not None:
            _validate_retry_after(self.retry_after)
        if self.failure_code is not None:
            object.__setattr__(
                self, "failure_code",
                _bounded_text(
                    self.failure_code,
                    name="failure_code",
                    maximum=MAX_FAILURE_TEXT,
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
