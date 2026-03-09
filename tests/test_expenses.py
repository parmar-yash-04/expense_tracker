from datetime import date


def test_create_expense(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    assert response.status_code == 201
    assert float(response.json()["amount"]) == 50.00


def test_create_expense_category_not_found(client, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": 99999,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    assert response.status_code == 400


def test_get_expenses(client, test_category, auth_headers):
    client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    
    response = client.get("/api/expenses", headers=auth_headers)
    assert response.status_code == 200


def test_get_expense_by_id(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    expense_id = response.json()["id"]
    
    response = client.get(f"/api/expenses?expense_id={expense_id}", headers=auth_headers)
    assert response.status_code == 200


def test_update_expense(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    expense_id = response.json()["id"]
    
    response = client.put(f"/api/expense/{expense_id}", json={
        "amount": 75.00
    }, headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 75.00


def test_delete_expense(client, test_category, auth_headers):
    response = client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    expense_id = response.json()["id"]
    
    response = client.delete(f"/api/expense/{expense_id}", headers=auth_headers)
    assert response.status_code == 204


def test_get_expense_summary(client, test_category, auth_headers):
    client.post("/api/expense", json={
        "category_id": test_category.id,
        "amount": 50.00,
        "merchant": "Test Store",
        "description": "Test expense",
        "transaction_date": str(date.today())
    }, headers=auth_headers)
    
    response = client.get("/api/summary", headers=auth_headers)
    assert response.status_code == 200
