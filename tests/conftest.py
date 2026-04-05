import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.worker.tasks import process_notification

# Setup SQLite in-memory for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    # Mock celery task to just do nothing instead of connecting to redis
    process_notification.apply_async = lambda *args, **kwargs: None
    
    # Mock rate_limiter to bypass redis checks
    import app.api.endpoints as endpoints
    from app.services.rate_limiter import check_rate_limit
    
    def override_rate_limit(user_id):
        pass # allow all
        
    endpoints.check_rate_limit = override_rate_limit
    
    with TestClient(app) as c:
        yield c
