import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from pathlib import Path
from ..core import settings

async def main():
    sql = Path(__file__).parent.parent.joinpath('sql/schema.sql').read_text()
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.execute(sql)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())