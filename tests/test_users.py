def test_create_user_success(client):
    response = client.post("/users/create", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"
    assert response.json()["email"] == "newuser@example.com"


def test_create_user_duplicate_username(client, test_user):
    response = client.post("/users/create", json={
        "username": "testuser",
        "email": "other@example.com",
        "password": "Password123"
    })
    assert response.status_code == 400


def test_create_user_duplicate_email(client, test_user):
    response = client.post("/users/create", json={
        "username": "otheruser",
        "email": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 400
