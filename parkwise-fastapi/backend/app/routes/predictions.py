from fastapi import APIRouter, HTTPException
from ..core import settings
import httpx

router = APIRouter(prefix="/v1/predictions")

@router.get("/{slot_id}")
async def get_prediction(slot_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.PREDICTOR_URL}/predict", json={"slot_id": slot_id})
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="predictor error")
    return resp.json()