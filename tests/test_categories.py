def test_create_category(client):
    response = client.post("/api/categories", json={
        "name": "Test Category",
        "description": "Test Description",
        "color": "#FF0000"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test Category"


def test_create_category_duplicate_name(client):
    client.post("/api/categories", json={
        "name": "Duplicate",
        "description": "First",
        "color": "#FF0000"
    })
    response = client.post("/api/categories", json={
        "name": "Duplicate",
        "description": "Second",
        "color": "#00FF00"
    })
    assert response.status_code == 400


def test_get_categories(client, test_category):
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_category_by_id(client, test_category):
    response = client.get(f"/api/categories/{test_category.id}")
    assert response.status_code == 200
    assert response.json()["name"] == test_category.name


def test_get_category_not_found(client):
    response = client.get("/api/categories/99999")
    assert response.status_code == 404


def test_update_category(client, test_category):
    response = client.put(f"/api/categories/{test_category.id}", json={
        "name": "Updated Category",
        "description": "Updated Description",
        "color": "#00FF00"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Category"


def test_delete_category(client, test_category):
    response = client.delete(f"/api/categories/{test_category.id}")
    assert response.status_code == 204
    
    response = client.get(f"/api/categories/{test_category.id}")
    assert response.status_code == 404
