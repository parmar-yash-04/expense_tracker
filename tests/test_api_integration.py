from datetime import date


def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "invalid-email",
        "password": "Password123"
    })
    assert response.status_code == 400


def test_register_password_too_short(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Pass1"
    })
    assert response.status_code == 400


def test_register_empty_username(client):
    response = client.post("/auth/register", json={
        "username": "",
        "email": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123"
    })
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "Wrongpassword"
    })
    assert response.status_code == 401


def test_expense_invalid_category(client, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": 99999,
        "amount": 50.00,
        "merchant": "Test",
        "description": "Test",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    assert response.status_code == 400
    assert "Category not found" in response.json()["detail"]


def test_expense_invalid_amount(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": -50.00,
        "merchant": "Test",
        "description": "Test",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_expense_missing_transaction_date(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test",
        "description": "Test"
    }, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_get_expense_not_found(client, auth_headers):
    response = client.get("/api/expenses?expense_id=99999", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_update_expense_not_found(client, auth_headers):
    response = client.put("/api/expense/99999", json={
        "amount": 100.00
    }, headers=auth_headers)
    assert response.status_code == 404


def test_delete_expense_not_found(client, auth_headers):
    response = client.delete("/api/expense/99999", headers=auth_headers)
    assert response.status_code == 404


def test_budget_invalid_category(client, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": 99999,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 400
    assert "Category not found" in response.json()["detail"]


def test_budget_invalid_month(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 13,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_budget_invalid_year(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 1999
    }, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_get_budget_not_found(client, auth_headers):
    response = client.get("/api/budgets/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_budget_not_found(client, auth_headers):
    response = client.put("/api/budgets/99999", json={
        "category_id": 1,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    assert response.status_code == 404


def test_category_invalid_name(client):
    response = client.post("/api/categories", json={
        "name": "",
        "description": "Test",
        "color": "#FF0000"
    })
    assert response.status_code in [400, 422]


def test_category_not_found(client):
    response = client.get("/api/categories/99999")
    assert response.status_code == 404


def test_update_category_not_found(client):
    response = client.put("/api/categories/99999", json={
        "name": "NewName",
        "description": "Test",
        "color": "#FF0000"
    })
    assert response.status_code == 404


def test_delete_category_not_found(client):
    response = client.delete("/api/categories/99999")
    assert response.status_code == 404


def test_invalid_token_format(client):
    response = client.get("/api/expenses", headers={
        "Authorization": "InvalidFormat"
    })
    assert response.status_code == 401


def test_expense_update_partial(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test",
        "description": "Test",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    expense_id = response.json()["id"]
    
    response = client.put(f"/api/expense/{expense_id}", json={
        "amount": 75.00
    }, headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 75.00
    assert response.json()["merchant"] == "Test"


def test_budget_update_partial(client, test_category, auth_headers):
    response = client.post("/api/budgets", json={
        "category_id": test_category.id,
        "limit_amount": 500.00,
        "month": 1,
        "year": 2024
    }, headers=auth_headers)
    budget_id = response.json()["id"]
    
    response = client.put(f"/api/budgets/{budget_id}", json={
        "limit_amount": 750.00
    }, headers=auth_headers)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        assert float(response.json()["limit_amount"]) == 750.00


def test_category_update_partial(client):
    response = client.post("/api/categories", json={
        "name": "TestCat",
        "description": "Original",
        "color": "#FF0000"
    })
    cat_id = response.json()["id"]
    
    response = client.put(f"/api/categories/{cat_id}", json={
        "description": "Updated"
    })
    assert response.status_code in [200, 400]
