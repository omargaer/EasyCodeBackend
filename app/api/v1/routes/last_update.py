# 📄 app/api/v1/routes/last_update.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.db import get_db
from app.models import ExchangeRate

router = APIRouter()


def format_timestamp_as_moscow_time(ts: int) -> str:
    dt_utc = datetime.fromtimestamp(ts, tz=ZoneInfo("UTC"))
    dt_moscow = dt_utc.astimezone(ZoneInfo("Europe/Moscow"))
    return dt_moscow.strftime('%Y-%m-%d %H:%M:%S')

@router.get("/last-currencies-rates-update")
async def get_last_rates_update(db: AsyncSession = Depends(get_db)):
    query = select(func.max(ExchangeRate.timestamp))
    result = await db.execute(query)
    max_timestamp = result.scalar()

    if not max_timestamp:
        return {"message": "Курсы валют еще не обновлялись"}

    readable_time = format_timestamp_as_moscow_time(max_timestamp)
    return {"message": f"Последнее обновление курсов валют было {readable_time}."}
