"""Function-level provenance tags and optional runtime call tracing."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar
import json


F = TypeVar("F", bound=Callable[..., Any])

_ROUTINE_TO_TARGET: dict[str, str] = {}
_TARGET_TO_ROUTINES: dict[str, tuple[str, ...]] = {}
_TRACE_EVENTS: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "_TRACE_EVENTS", default=None
)


def _normalize_routines(routines: Iterable[str]) -> tuple[str, ...]:
    out: list[str] = []
    for name in routines:
        normalized = str(name).strip().lower()
        if normalized and normalized not in out:
            out.append(normalized)
    return tuple(out)


def fortran_provenance(*routine_names: str) -> Callable[[F], F]:
    """Tag a Python function with one or more source Fortran routine names."""

    names = _normalize_routines(routine_names)

    def _decorate(func: F) -> F:
        target = f"{func.__module__}.{func.__qualname__}"
        if names:
            _TARGET_TO_ROUTINES[target] = names
            for name in names:
                _ROUTINE_TO_TARGET[name] = target
        setattr(func, "__fortran_routines__", names)

        @wraps(func)
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            events = _TRACE_EVENTS.get()
            if events is not None:
                events.append(
                    {
                        "python_target": target,
                        "fortran_routines": list(names),
                    }
                )
            return func(*args, **kwargs)

        return _wrapped  # type: ignore[return-value]

    return _decorate


@contextmanager
def capture_trace_events() -> list[dict[str, Any]]:
    """Capture provenance-decorated function calls in the current context."""

    events: list[dict[str, Any]] = []
    token = _TRACE_EVENTS.set(events)
    try:
        yield events
    finally:
        _TRACE_EVENTS.reset(token)


def write_trace_log(
    path: str | Path,
    *,
    events: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write call-trace events to JSON for audit/reproducibility."""

    payload = {
        "trace_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_count": len(events),
        "events": events,
    }
    if metadata:
        payload["metadata"] = dict(metadata)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def record_trace_event(python_target: str, fortran_routines: Iterable[str]) -> None:
    """Append an explicit trace event when a capture context is active."""

    events = _TRACE_EVENTS.get()
    if events is None:
        return
    events.append(
        {
            "python_target": str(python_target),
            "fortran_routines": list(_normalize_routines(fortran_routines)),
        }
    )


def provenance_registry() -> dict[str, str]:
    """Return routine-name -> python-target mapping from decorators."""

    return dict(_ROUTINE_TO_TARGET)


def target_routines_registry() -> dict[str, tuple[str, ...]]:
    """Return python-target -> routine-name mapping from decorators."""

    return dict(_TARGET_TO_ROUTINES)


__all__ = [
    "capture_trace_events",
    "fortran_provenance",
    "provenance_registry",
    "record_trace_event",
    "target_routines_registry",
    "write_trace_log",
]
