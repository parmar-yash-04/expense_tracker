def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"
    assert response.json()["email"] == "newuser@example.com"


def test_register_duplicate_username(client, test_user):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "other@example.com",
        "password": "Password123"
    })
    assert response.status_code == 400
    assert "Username" in response.json()["detail"] or "username" in response.json()["detail"]


def test_register_duplicate_email(client, test_user):
    response = client.post("/auth/register", json={
        "username": "otheruser",
        "email": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 400
    assert "Email" in response.json()["detail"] or "email" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "Testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "Wrongpassword123"
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "Password123"
    })
    assert response.status_code == 401
