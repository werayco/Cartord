from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
from app.routers import inventory_router, admin_router
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
    print(f.renderText('Inventory Service'))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

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
    return {"message": "Welcome to the Inventory Service", "version": "1.0.0"}

app.include_router(inventory_router)
app.include_router(admin_router)