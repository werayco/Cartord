from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
from app.routers import order_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    f = Figlet(font='slant')
    print(f.renderText('Order Service'))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def root():
    return {"message": "Welcome to the Order Service", "version": "1.0.0"}

app.include_router(order_router)