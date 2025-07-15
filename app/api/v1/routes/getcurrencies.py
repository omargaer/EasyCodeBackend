from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiohttp
from datetime import datetime, date

from app.db import get_db
from app.models import Currency, ExchangeRate

import os

API_KEY = os.environ.get("API_KEY")
router = APIRouter()

API_URL = f"https://api.exchangeratesapi.io/v1/latest?access_key={API_KEY}"


@router.post("/get-currencies")
async def get_all_currencies(db: AsyncSession = Depends(get_db)):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=resp.status, detail="Ошибка при соединении с валютным API")
            data = await resp.json()

    if not data.get("success"):
        raise HTTPException(status_code=400, detail="Ответ API не содержит success: true")

    base_code = data["base"]
    rates = data["rates"]
    rate_date = date.fromisoformat(data["date"])
    timestamp = data["timestamp"]

    currency_codes = list(rates.keys()) + [base_code]

    result = await db.execute(select(Currency.code))
    existing_codes = {row[0] for row in result.all()}

    new_codes = set(currency_codes) - existing_codes
    for code in new_codes:
        db.add(Currency(code=code))

    await db.commit()

    result = await db.execute(select(Currency).where(Currency.code.in_(currency_codes)))
    currencies = result.scalars().all()
    code_to_id = {c.code: c.id for c in currencies}

    base_currency_id = code_to_id[base_code]

    for code, rate in rates.items():
        if code == base_code:
            continue

        target_currency_id = code_to_id[code]

        result = await db.execute(select(ExchangeRate).where(
            ExchangeRate.base_currency_id == base_currency_id,
            ExchangeRate.target_currency_id == target_currency_id,
            ExchangeRate.date == rate_date
        ))
        record = result.scalar_one_or_none()

        if record:
            record.rate_value = rate
            record.timestamp = timestamp
        else:
            db.add(ExchangeRate(
                base_currency_id=base_currency_id,
                target_currency_id=target_currency_id,
                rate_value=rate,
                date=rate_date,
                timestamp=timestamp
            ))

    await db.commit()

    return {"detail": "Инициализация базы завершена успешно"}
