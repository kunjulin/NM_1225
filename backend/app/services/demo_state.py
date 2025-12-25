from __future__ import annotations

from typing import Dict


_acting_roles: Dict[str, str] = {}


def set_acting_role(subject: str, acting_role: str) -> None:
    _acting_roles[subject] = acting_role


def get_acting_role(subject: str) -> str | None:
    return _acting_roles.get(subject)
