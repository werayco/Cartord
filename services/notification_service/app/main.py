import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.kafka.consumer import kafka_manager
from pyfiglet import Figlet
from app.services.telemetry import setup_telemetry

f = Figlet(font='slant')

@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(kafka_manager.consume())
    print(f.renderText('Notification Service'))
    yield
    kafka_manager.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
setup_telemetry(app)

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the Notification Service", "version": "1.0.0"}