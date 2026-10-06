"""Synthetic membership payloads shared by offline contract tests."""

from typing import Any


def membership(
    membership_id: int = 20,
    *,
    project_id: int = 7,
    user_id: int = 10,
    group: bool = False,
    inherited: bool = False,
    role_id: int = 4,
) -> dict[str, Any]:
    return {
        "id": membership_id,
        "project": {"id": project_id, "name": "Demo"},
        "group" if group else "user": {"id": user_id, "name": "Principal"},
        "roles": [{"id": role_id, "name": f"Role {role_id}", "inherited": inherited}],
    }
