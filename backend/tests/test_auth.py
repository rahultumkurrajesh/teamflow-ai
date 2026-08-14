"""Tests for authentication and role checks.

The service tests pass a fake repository through the constructor, which is the
payoff of the dependency injection choice made in Stage 2: none of these need
Postgres, so they run in milliseconds and need no service container in CI.
"""
import uuid

import pytest

from app.core.exceptions import AuthError
from app.core.roles import at_least, rank
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.services.auth import AuthService


class FakeUserRepository:
    """Stands in for UserRepository, with the two methods AuthService calls."""

    def __init__(self, users: list[User] | None = None) -> None:
        self._users = users or []

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users if u.email == email), None)

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((u for u in self._users if u.id == user_id), None)


@pytest.fixture
def user() -> User:
    return User(
        id=uuid.uuid4(),
        email="rahul@example.com",
        full_name="Rahul Tumkur Rajesh",
        hashed_password=hash_password("correct-horse-battery"),
        role=UserRole.member,
        is_active=True,
    )


@pytest.fixture
def service(user: User) -> AuthService:
    return AuthService(FakeUserRepository([user]))  # type: ignore[arg-type]


# Password hashing


def test_hash_is_not_the_password() -> None:
    hashed = hash_password("supersecret")
    assert hashed != "supersecret"
    assert verify_password("supersecret", hashed)


def test_wrong_password_is_rejected() -> None:
    assert not verify_password("wrong", hash_password("supersecret"))


def test_same_password_hashes_differently() -> None:
    """bcrypt salts every hash, so two hashes of one password must differ."""
    assert hash_password("supersecret") != hash_password("supersecret")


def test_malformed_hash_returns_false_rather_than_raising() -> None:
    assert not verify_password("anything", "not-a-bcrypt-hash")


# Tokens


def test_access_token_round_trips() -> None:
    uid = str(uuid.uuid4())
    payload = decode_token(create_access_token(uid, "admin"), expected_type="access")
    assert payload["sub"] == uid
    assert payload["role"] == "admin"


def test_refresh_token_rejected_where_access_expected() -> None:
    token = create_refresh_token(str(uuid.uuid4()))
    with pytest.raises(AuthError):
        decode_token(token, expected_type="access")


def test_refresh_token_carries_no_role() -> None:
    payload = decode_token(
        create_refresh_token(str(uuid.uuid4())), expected_type="refresh"
    )
    assert "role" not in payload


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(str(uuid.uuid4()), "member")
    with pytest.raises(AuthError):
        decode_token(token[:-2] + "xx", expected_type="access")


# Role ordering


@pytest.mark.parametrize(
    ("held", "required", "allowed"),
    [
        ("admin", "admin", True),
        ("admin", "member", True),
        ("member", "member", True),
        ("member", "admin", False),
    ],
)
def test_role_ordering(held: str, required: str, allowed: bool) -> None:
    assert at_least(held, required) is allowed


def test_unknown_role_ranks_lowest() -> None:
    """An unrecognised role must fail closed, never outrank a real one."""
    assert rank("wizard") < rank("member")
    assert not at_least("wizard", "member")


# Service


def test_login_returns_a_pair(service: AuthService, user: User) -> None:
    tokens = service.login(user.email, "correct-horse-battery")
    assert tokens.access_token and tokens.refresh_token
    assert tokens.token_type == "bearer"
    assert tokens.expires_in > 0


def test_login_embeds_the_role(service: AuthService, user: User) -> None:
    tokens = service.login(user.email, "correct-horse-battery")
    payload = decode_token(tokens.access_token, expected_type="access")
    assert payload["role"] == "member"


def test_login_with_wrong_password_fails(service: AuthService, user: User) -> None:
    with pytest.raises(AuthError):
        service.login(user.email, "definitely-not-it")


def test_unknown_email_gives_the_same_error(service: AuthService) -> None:
    """Identical failure for unknown email and bad password: no enumeration."""
    with pytest.raises(AuthError):
        service.login("nobody@example.com", "whatever123")


def test_inactive_user_cannot_log_in(user: User) -> None:
    user.is_active = False
    service = AuthService(FakeUserRepository([user]))  # type: ignore[arg-type]
    with pytest.raises(AuthError):
        service.login(user.email, "correct-horse-battery")


def test_refresh_reflects_a_role_change(service: AuthService, user: User) -> None:
    """A promotion must take effect on the next refresh, not at token expiry."""
    tokens = service.login(user.email, "correct-horse-battery")
    user.role = UserRole.admin
    new_tokens = service.refresh(tokens.refresh_token)
    payload = decode_token(new_tokens.access_token, expected_type="access")
    assert payload["role"] == "admin"


def test_refresh_fails_for_deactivated_user(service: AuthService, user: User) -> None:
    tokens = service.login(user.email, "correct-horse-battery")
    user.is_active = False
    with pytest.raises(AuthError):
        service.refresh(tokens.refresh_token)


def test_access_token_cannot_be_used_to_refresh(service: AuthService, user: User) -> None:
    tokens = service.login(user.email, "correct-horse-battery")
    with pytest.raises(AuthError):
        service.refresh(tokens.access_token)
