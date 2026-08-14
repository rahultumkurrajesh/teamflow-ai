"""Role ordering for authorisation checks.

The roles themselves live on the User model (UserRole). This module only adds
the ordering, and it keys off the enum's string *values* rather than importing
the model, so app.core stays free of any dependency on app.models.

Ordering matters because it lets a route say "member or above" instead of
listing every role that qualifies. Add a role to the enum and you only touch
_RANK here, not every endpoint.
"""
from collections.abc import Iterable

# Higher number means more authority. Keys are UserRole values.
_RANK: dict[str, int] = {
    "member": 0,
    "admin": 1,
}


def rank(role: str) -> int:
    """Authority level of a role. Unknown roles rank lowest, never highest.

    Failing closed matters: if a role string appears in the database that this
    code does not know about, it must not accidentally outrank an admin.
    """
    return _RANK.get(str(role), -1)


def at_least(role: str, required: str) -> bool:
    """True when `role` carries at least as much authority as `required`."""
    return rank(role) >= rank(required)


def known_roles() -> Iterable[str]:
    return _RANK.keys()
