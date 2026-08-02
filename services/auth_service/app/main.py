from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from app.controllers.employee_controller import EmployeeController
from fastapi.middleware.cors import CORSMiddleware
from pyfiglet import Figlet
import redis
from app.db.redis_client import redis_client
from app.routers import employee_router, user_router
import asyncio

f = Figlet(font='slant')

@asynccontextmanager
async def lifespan(app: FastAPI):

    print(f.renderText('Auth Service'))
    app.state.redis = redis_client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    response = await EmployeeController.run()
    print(response)
    
    yield
    app.state.redis.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)

@app.get("/api/v1/health")
async def root():
    try:
        app.state.redis.ping()
        redis_status = "connected"
    except redis.exceptions.RedisError:
        redis_status = "disconnected"

    return {
        "message": "Welcome to the Auth Service",
        "version": "1.0.0",
        "redis": redis_status,
    }


app.include_router(employee_router)
app.include_router(user_router)