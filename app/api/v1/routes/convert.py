# app/api/v1/routes/convert.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field, condecimal
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from app.db import get_db
from app.models import ExchangeRate, Currency

router = APIRouter()

class ConvertRequest(BaseModel):
    from_currency: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    to_currency: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    amount: condecimal(gt=0)

class ConvertResponse(BaseModel):
    result: condecimal(gt=0, decimal_places=2)

async def convert_currency(
    db: AsyncSession,
    from_code: str,
    to_code: str,
    amount: Decimal
) -> Decimal:
    from_code = from_code.upper()
    to_code = to_code.upper()
    base_code = "EUR"  # внутренняя опорная валюта (можно изменить на USD, если в базе иначе)

    # Загружаем все валюты
    result = await db.execute(select(Currency))
    currencies = result.scalars().all()
    code_to_id = {c.code.upper(): c.id for c in currencies}

    if from_code not in code_to_id or to_code not in code_to_id or base_code not in code_to_id:
        raise HTTPException(status_code=400, detail="Одна или несколько валют не найдены")

    base_currency_id = code_to_id[base_code]
    from_id = code_to_id[from_code]
    to_id = code_to_id[to_code]

    # Находим последний timestamp
    result = await db.execute(select(func.max(ExchangeRate.timestamp)))
    latest_ts = result.scalar()
    if not latest_ts:
        raise HTTPException(status_code=404, detail="Курсы валют пока не загружены")

    # Загружаем все курсы base→X (EUR → ...)
    result = await db.execute(
        select(ExchangeRate).where(
            ExchangeRate.timestamp == latest_ts,
            ExchangeRate.base_currency_id == base_currency_id
        )
    )
    rates = result.scalars().all()
    # {target_currency_id: rate_value}
    rate_map = {r.target_currency_id: Decimal(r.rate_value) for r in rates}

    # Прямая конвертация через base-валюту
    if from_id in rate_map and to_id in rate_map:
        from_per_base = rate_map[from_id]
        to_per_base = rate_map[to_id]
        eur_amount = amount / from_per_base
        converted = eur_amount * to_per_base
        return converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Попробуем найти через любую промежуточную валюту (X): FROM→X→TO
    for intermediate_id, inter_rate in rate_map.items():
        if intermediate_id in (from_id, to_id):
            continue
        # Проверяем, можем ли добраться из from → base → intermediate → base → to
        # Т.е. есть и from_id, и intermediate_id, и to_id в rate_map
        if from_id in rate_map and intermediate_id in rate_map and to_id in rate_map:
            try:
                from_per_base = rate_map[from_id]
                intermediate_per_base = rate_map[intermediate_id]
                to_per_base = rate_map[to_id]
                # FROM → EUR → INTERMEDIATE
                eur_amount = amount / from_per_base
                inter_amount = eur_amount * intermediate_per_base
                # INTERMEDIATE → EUR → TO
                eur_again = inter_amount / intermediate_per_base
                converted = eur_again * to_per_base
                return converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except Exception:
                continue

    # Пока что реализован только "через одну базовую"
    raise HTTPException(status_code=404, detail="Нет доступного маршрута для конвертации — проверьте актуальность курсов валют")

@router.post("/convert", response_model=ConvertResponse)
async def convert_ajax(data: ConvertRequest, db: AsyncSession = Depends(get_db)):
    if data.from_currency == data.to_currency:
        return ConvertResponse(result=data.amount.quantize(Decimal("0.01"), ROUND_HALF_UP))

    result = await convert_currency(
        db,
        data.from_currency,
        data.to_currency,
        data.amount
    )

    return ConvertResponse(result=result)
