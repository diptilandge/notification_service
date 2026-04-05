from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.endpoints import router
from app.db.session import engine, Base
import app.models.notification # To ensure metadata gathers it
import app.models.preference

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema for demonstration
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-channel notification service backend with priorities and tracking.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, tags=["notifications"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
