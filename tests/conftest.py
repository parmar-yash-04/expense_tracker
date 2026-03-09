import pytest
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///./test_database.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    from app.database import Base, get_db
    from main import app
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clear_rate_limits():
    from app.rate_limiter import get_redis_client
    redis_client = get_redis_client()
    if redis_client:
        try:
            for key in redis_client.scan_iter("rate_limit:*"):
                redis_client.delete(key)
        except Exception:
            pass
    yield


@pytest.fixture
def test_user(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Testpassword123"
    })
    return response.json()


@pytest.fixture
def auth_token(client, test_user):
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "Testpassword123"
    })
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_category(db):
    from app.models import Category
    category = Category(name="Food", description="Food expenses", color="#FF0000")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
