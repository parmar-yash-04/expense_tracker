from datetime import date


def test_full_user_flow_register_login_create_expense_retrieve(client):
    register_response = client.post("/auth/register", json={
        "username": "flowuser",
        "email": "flow@example.com",
        "password": "Password123"
    })
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]
    
    login_response = client.post("/auth/login", data={
        "username": "flow@example.com",
        "password": "Password123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    category_response = client.post("/api/categories", json={
        "name": "Groceries",
        "description": "Grocery items",
        "color": "#00FF00"
    })
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]
    
    expense_response = client.post("/api/expense", json={
        "category_id": category_id,
        "amount": 50.00,
        "merchant": "Walmart",
        "description": "Weekly groceries",
        "transaction_date": str(date.today())
    }, headers=headers)
    assert expense_response.status_code == 201
    expense_id = expense_response.json()["id"]
    
    retrieve_response = client.get("/api/expenses", headers=headers)
    assert retrieve_response.status_code == 200
    assert len(retrieve_response.json()) >= 1
    
    summary_response = client.get("/api/summary", headers=headers)
    assert summary_response.status_code == 200
    assert "total_spending" in summary_response.json()


def test_multi_user_data_isolation(client):
    client.post("/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "Password123"
    })
    login1 = client.post("/auth/login", data={
        "username": "user1@example.com",
        "password": "Password123"
    })
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    client.post("/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "Password123"
    })
    login2 = client.post("/auth/login", data={
        "username": "user2@example.com",
        "password": "Password123"
    })
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    cat1 = client.post("/api/categories", json={
        "name": "User1Cat",
        "description": "Test",
        "color": "#FF0000"
    }, headers=headers1)
    cat1_id = cat1.json()["id"]
    
    client.post("/api/expense", json={
        "category_id": cat1_id,
        "amount": 100.00,
        "merchant": "Test",
        "description": "User1 expense",
        "transaction_date": str(date.today())
    }, headers=headers1)
    
    cat2 = client.post("/api/categories", json={
        "name": "User2Cat",
        "description": "Test",
        "color": "#00FF00"
    }, headers=headers2)
    cat2_id = cat2.json()["id"]
    
    client.post("/api/expense", json={
        "category_id": cat2_id,
        "amount": 200.00,
        "merchant": "Test",
        "description": "User2 expense",
        "transaction_date": str(date.today())
    }, headers=headers2)
    
    user1_expenses = client.get("/api/expenses", headers=headers1)
    assert len(user1_expenses.json()) == 1
    assert float(user1_expenses.json()[0]["amount"]) == 100.00
    
    user2_expenses = client.get("/api/expenses", headers=headers2)
    assert len(user2_expenses.json()) == 1
    assert float(user2_expenses.json()[0]["amount"]) == 200.00
    
    summary1 = client.get("/api/summary", headers=headers1)
    assert float(summary1.json()["total_spending"]) == 100.00
    
    summary2 = client.get("/api/summary", headers=headers2)
    assert float(summary2.json()["total_spending"]) == 200.00


def test_authentication_with_invalid_token(client):
    response = client.get("/api/expenses", headers={
        "Authorization": "Bearer invalid_token_here"
    })
    assert response.status_code == 401


def test_authentication_without_token(client):
    response = client.get("/api/expenses")
    assert response.status_code == 401


def test_protected_endpoint_without_auth(client):
    endpoints = [
        "/api/expenses",
        "/api/budgets",
        "/api/summary"
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403]


def test_unauthorized_access_to_other_user_expense(client):
    client.post("/auth/register", json={
        "username": "owner",
        "email": "owner@example.com",
        "password": "Password123"
    })
    owner_login = client.post("/auth/login", data={
        "username": "owner@example.com",
        "password": "Password123"
    })
    owner_token = owner_login.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    
    cat = client.post("/api/categories", json={
        "name": "TestCat",
        "description": "Test",
        "color": "#FF0000"
    }, headers=owner_headers)
    cat_id = cat.json()["id"]
    
    expense = client.post("/api/expense", json={
        "category_id": cat_id,
        "amount": 50.00,
        "merchant": "Test",
        "description": "Owner expense",
        "transaction_date": str(date.today())
    }, headers=owner_headers)
    expense_id = expense.json()["id"]
    
    client.post("/auth/register", json={
        "username": "attacker",
        "email": "attacker@example.com",
        "password": "Password123"
    })
    attacker_login = client.post("/auth/login", data={
        "username": "attacker@example.com",
        "password": "Password123"
    })
    attacker_token = attacker_login.json()["access_token"]
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
    
    response = client.get(f"/api/expenses?expense_id={expense_id}", headers=attacker_headers)
    assert response.status_code == 200
    expenses = response.json()
    assert all(e["id"] != expense_id for e in expenses)
