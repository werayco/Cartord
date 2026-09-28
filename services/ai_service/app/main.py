import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
from app.routers.document import router as document_router
from app.routers.websocket_router import router as chat_router
from app.services.telemetry import setup_telemetry
from app.kafka.consumer import kafka_manager
from app.core.config import settings
import sentry_sdk

if settings.SENTRY_DSN and "@" in settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.01,
        auto_session_tracking=False,
    )

f = Figlet(font='slant')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f.renderText('AI Service'))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    consumer_task = asyncio.create_task(kafka_manager.consume())
    yield
    kafka_manager.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
setup_telemetry(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOW_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the AI Service", "version": "1.0.0"}

app.include_router(document_router)
app.include_router(chat_router)