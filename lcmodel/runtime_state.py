"""Typed runtime-state container for legacy-bridge semantics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class RuntimeState(dict[str, Any]):
    """Mutable mapping used by scaffold/override bridge with typed helpers.

    The legacy bridge expects a dict-like object. This subclass keeps that
    compatibility while adding explicit entry points for common state fields.
    """

    @classmethod
    def coerce(cls, state: Mapping[str, Any] | None) -> "RuntimeState":
        if isinstance(state, cls):
            return state
        out = cls()
        if state is not None:
            out.update(state)
        return out

    @property
    def datat(self) -> list[complex] | None:
        value = self.get("datat")
        return value if isinstance(value, list) else None

    @datat.setter
    def datat(self, value: list[complex]) -> None:
        self["datat"] = value

    @property
    def dataf(self) -> list[complex] | None:
        value = self.get("dataf")
        return value if isinstance(value, list) else None

    @dataf.setter
    def dataf(self, value: list[complex]) -> None:
        self["dataf"] = value

    def mark_placeholder(self, routine_name: str) -> None:
        entries = self.get("placeholder_overrides")
        if not isinstance(entries, list):
            entries = []
            self["placeholder_overrides"] = entries
        entries.append(routine_name)
