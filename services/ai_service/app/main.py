from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
from app.routers.document import router as document_router
from app.routers.websocket_router import router as chat_router
from app.services.telemetry import setup_telemetry

f = Figlet(font='slant')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f.renderText('AI Service'))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
setup_telemetry(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the AI Service", "version": "1.0.0"}

app.include_router(document_router)
app.include_router(chat_router)