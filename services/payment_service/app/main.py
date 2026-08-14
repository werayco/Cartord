import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import engine, Base
from app.routers.payment_router import router as payment_router
from app import models  # noqa: F401  <-- ensures all models register with Base.metadata
from app.kafka.consumer import kafka_manager
from pyfiglet import Figlet
f = Figlet(font='slant')

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    consumer_task = asyncio.create_task(kafka_manager.consume())
    print(f.renderText('Payment Service'))
    yield
    kafka_manager.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.include_router(payment_router)

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the Payment Service", "version": "1.0.0"}