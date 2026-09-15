def test_signup_then_login(client):
    resp = client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "username": "alice", "password": "password123"},
    )
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp = client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_signup_duplicate_email_rejected(client):
    client.post("/api/auth/signup", json={"email": "b@example.com", "username": "bob", "password": "password123"})
    resp = client.post(
        "/api/auth/signup", json={"email": "b@example.com", "username": "bob2", "password": "password123"}
    )
    assert resp.status_code == 400


def test_login_wrong_password_rejected(client):
    client.post("/api/auth/signup", json={"email": "c@example.com", "username": "carol", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "c@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401


def test_long_password_does_not_500(client):
    """Regression test: bcrypt raises on >72-byte inputs unless truncated first.
    Stays under the schema's 128-char max while exceeding bcrypt's 72-byte limit."""
    long_password = "x" * 100
    resp = client.post(
        "/api/auth/signup", json={"email": "d@example.com", "username": "dave", "password": long_password}
    )
    assert resp.status_code == 201

    resp = client.post("/api/auth/login", json={"email": "d@example.com", "password": long_password})
    assert resp.status_code == 200
