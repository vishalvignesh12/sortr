from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .core import settings

# For SQLite, we need to use the async dialect
if settings.DATABASE_URL.startswith("sqlite"):
    # Convert sqlite:// to sqlite+aiosqlite:// 
    db_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(
        db_url,
        echo=False,  # Set to False in production
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"check_same_thread": False}  # Required for SQLite
    )
else:
    # Create async engine for PostgreSQL
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session