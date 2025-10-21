import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from ..core import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        for i in range(1, 101):
            slot_id = f"slot_{i:03d}"
            await conn.execute(text("INSERT INTO slots (slot_id) VALUES (:slot_id) ON CONFLICT DO NOTHING"), {'slot_id': slot_id})
            await conn.execute(text("INSERT INTO slot_status (slot_id, occupied) VALUES (:slot_id, false) ON CONFLICT DO NOTHING"), {'slot_id': slot_id})
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())