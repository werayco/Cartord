import asyncio
from fastapi import FastAPI
from app.routers import search_router
from pyfiglet import Figlet
from app.services import elasticsearch_client, kafka_manager
from contextlib import asynccontextmanager
from app.services.telemetry import setup_telemetry
from app.core.config import settings
import sentry_sdk

if settings.SENTRY_DSN and "@" in settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.01,
        auto_session_tracking=False,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    f = Figlet(font='slant')
    print(f.renderText('Search Service'))
    await elasticsearch_client._ensure_index()

    consumer_task = asyncio.create_task(kafka_manager.consume())
    yield
    kafka_manager.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
setup_telemetry(app)
app.include_router(search_router)

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the Search Service", "version": "1.0.0"}