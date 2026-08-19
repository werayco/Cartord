from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.PAYMENT_DATABASE_URL, echo=True,pool_pre_ping=True,
    pool_recycle=1800, 
    pool_size=5,
    max_overflow=10,)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session