import asyncio
import redis.asyncio as aioredis
from .core import settings
from sqlalchemy import text
from .db import engine
from datetime import datetime
import httpx

async def expire_holds():
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE bookings SET status='expired' WHERE status='holding' AND hold_until < now()"))
        await conn.execute(text("UPDATE slot_status SET reserved_until = NULL WHERE reserved_until < now()"))

async def prediction_consumer():
    r = aioredis.from_url(settings.REDIS_URL)
    async with httpx.AsyncClient() as client:
        while True:
            res = await r.brpop("predict_queue", timeout=5)
            if res:
                _, slot_id = res
                # call predictor
                try:
                    pr = await client.post(f"{settings.PREDICTOR_URL}/predict", json={"slot_id": slot_id.decode()})
                    if pr.status_code == 200:
                        data = pr.json()
                        # persist prediction
                        async with engine.begin() as conn:
                            await conn.execute(text("UPDATE slot_status SET predicted_free_minutes = :m, prediction_confidence = :c WHERE slot_id = :slot_id"),
                                               {'m': data.get('predicted_free_minutes'), 'c': data.get('confidence'), 'slot_id': slot_id.decode()})
                except Exception as e:
                    print("predictor call failed", e)
            await asyncio.sleep(0.01)

async def start_workers():
    while True:
        try:
            await expire_holds()
            await asyncio.sleep(5)
        except Exception as e:
            print("expire job failed", e)
        await asyncio.sleep(1)

# to run the consumer concurrently use in uvicorn startup event or run as separate process