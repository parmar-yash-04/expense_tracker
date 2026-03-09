from datetime import date


def test_create_budget(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 201
    assert float(response.json()["limit_amount"]) == 500.00


def test_create_budget_category_not_found(client, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": 99999,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 400


def test_get_budgets(client, test_category, auth_headers):
    client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    
    response = client.get("/api/budgets", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_budget_by_id(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    budget_id = response.json()["id"]
    
    response = client.get(f"/api/budgets/{budget_id}", headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["limit_amount"]) == 500.00


def test_update_budget(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    budget_id = response.json()["id"]
    
    response = client.put(f"/api/budgets/{budget_id}", json={
        "category_id": test_category.id,
        "limit_amount": 750.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["limit_amount"]) == 750.00


def test_delete_budget(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    budget_id = response.json()["id"]
    
    response = client.delete(f"/api/budgets/{budget_id}", headers=auth_headers)
    assert response.status_code == 204


def test_create_budget_duplicate(client, test_category, auth_headers):
    client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 600.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 400
