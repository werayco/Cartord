from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
from app.routers import order_router
from app.services.telemetry import setup_telemetry
from app.db.redis_client import redis_client
import redis
from confluent_kafka.admin import AdminClient
from confluent_kafka import KafkaException
import asyncio
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    f = Figlet(font='slant')
    print(f.renderText('Order Service'))
    app.state.redis = redis_client
    app.state.kafka_admin = AdminClient({
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS
    })
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    app.state.redis.close()

app = FastAPI(lifespan=lifespan)
setup_telemetry(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def root():
    try:
        app.state.redis.ping()
        redis_status = "connected"
    except redis.exceptions.RedisError:
        redis_status = "disconnected"

    try:
        metadata = await asyncio.to_thread(
            app.state.kafka_admin.list_topics, timeout=5
        )
        kafka_status = "connected" if metadata.brokers else "disconnected"
    except KafkaException:
        kafka_status = "disconnected"
    except Exception:
        kafka_status = "disconnected"

    return {
        "message": "Welcome to the Order Service",
        "version": "1.0.0",
        "redis": redis_status,
        "kafka": kafka_status,
    }

app.include_router(order_router)