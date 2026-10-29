import pytest
from werkzeug.security import check_password_hash

from database.db import get_db

VALID = {"name": "Asha Rao", "email": "asha@example.com", "password": "secret123"}


def _users(where="1=1", params=()):
    conn = get_db()
    try:
        return conn.execute(f"SELECT * FROM users WHERE {where}", params).fetchall()
    finally:
        conn.close()


def _count():
    return len(_users())


def _post(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


def test_get_register_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'name="email"' in response.data


def test_valid_registration_redirects_to_login(client):
    response = _post(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert len(_users("email = ?", ("asha@example.com",))) == 1


def test_password_is_hashed(client):
    _post(client)
    user = _users("email = ?", ("asha@example.com",))[0]
    assert user["password_hash"] != VALID["password"]
    assert check_password_hash(user["password_hash"], VALID["password"])


def test_email_is_trimmed_and_lowercased(client):
    _post(client, email="  Test@Example.COM ")
    assert len(_users("email = ?", ("test@example.com",))) == 1


def test_duplicate_of_seeded_user_rejected(client):
    before = _count()
    response = _post(client, email="demo@spendly.com")
    assert response.status_code == 400
    assert b"An account with this email already exists." in response.data
    assert _count() == before


def test_duplicate_email_different_case_rejected(client):
    _post(client)
    before = _count()
    response = _post(client, email="ASHA@Example.com")
    assert response.status_code == 400
    assert b"An account with this email already exists." in response.data
    assert _count() == before


def test_short_password_rejected(client):
    before = _count()
    response = _post(client, password="short")
    assert response.status_code == 400
    assert b"Password must be at least 8 characters." in response.data
    assert _count() == before


@pytest.mark.parametrize("field", ["name", "email", "password"])
def test_empty_field_rejected(client, field):
    before = _count()
    response = _post(client, **{field: ""})
    assert response.status_code == 400
    assert b"All fields are required." in response.data
    assert _count() == before


def test_whitespace_only_name_rejected(client):
    before = _count()
    response = _post(client, name="   ")
    assert response.status_code == 400
    assert b"All fields are required." in response.data
    assert _count() == before


@pytest.mark.parametrize("email", ["abc", "a@b", "@example.com", "a@.", "@"])
def test_invalid_email_rejected(client, email):
    before = _count()
    response = _post(client, email=email)
    assert response.status_code == 400
    assert b"Enter a valid email address." in response.data
    assert _count() == before


def test_form_prefilled_on_error_but_not_password(client):
    response = _post(client, password="short")
    html = response.data.decode()
    assert 'value="Asha Rao"' in html
    assert 'value="asha@example.com"' in html
    assert "short" not in html.replace("Password must be at least 8 characters.", "")


def test_sql_injection_in_email_does_not_alter_database(client):
    before = _count()
    response = _post(client, email="'; DROP TABLE users;--")
    assert response.status_code == 400
    assert _count() == before
