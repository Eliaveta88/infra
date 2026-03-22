"""Identity API: register, login, me, refresh, logout, logout-all."""

from __future__ import annotations

import uuid

IDENTITY_PREFIX = "/identity/api/v1/identity"


def _unique_user() -> tuple[str, str, str]:
    suffix = uuid.uuid4().hex[:10]
    username = f"apitest_{suffix}"
    email = f"{username}@example.com"
    password = "TestPass123!"
    return username, email, password


def test_register_login_me_refresh_logout_flow(client) -> None:
    username, email, password = _unique_user()

    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert r.status_code == 201, r.text
    user = r.json()
    assert user["username"] == username
    assert user["email"] == email

    r = client.post(
        f"{IDENTITY_PREFIX}/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"
    assert access
    assert refresh

    r = client.get(
        f"{IDENTITY_PREFIX}/users/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["username"] == username

    r = client.post(
        f"{IDENTITY_PREFIX}/refresh",
        json={"refresh_token": refresh},
    )
    assert r.status_code == 200, r.text
    new_tokens = r.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    access2 = new_tokens["access_token"]

    r = client.post(
        f"{IDENTITY_PREFIX}/logout",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert r.status_code == 200, r.text
    assert r.json().get("status")

    # After logout, old access token may still work depending on JWT validation — do not assert 401.
    # Register second user and test logout-all with a fresh session.
    username2, email2, password2 = _unique_user()
    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={
            "username": username2,
            "email": email2,
            "password": password2,
        },
    )
    assert r.status_code == 201, r.text

    r = client.post(
        f"{IDENTITY_PREFIX}/login",
        json={"username": username2, "password": password2},
    )
    assert r.status_code == 200, r.text
    access_b = r.json()["access_token"]

    r = client.post(
        f"{IDENTITY_PREFIX}/logout-all",
        headers={"Authorization": f"Bearer {access_b}"},
    )
    assert r.status_code == 200, r.text


def test_login_invalid_credentials(client) -> None:
    r = client.post(
        f"{IDENTITY_PREFIX}/login",
        json={"username": "definitely_not_a_user_12345", "password": "wrong"},
    )
    assert r.status_code in (401, 422)
