from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
from app.db import get_db
from app.models import Currency
from app.crud import get_all_currencies, update_rates
from app.services.exchangerates import fetch_exchange_rates

router = APIRouter()
API_KEY = os.getenv("API_KEY")


@router.post("/update-rates")
async def update_rates_endpoint(db: AsyncSession = Depends(get_db)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY не задан")

    # Получаем актуальный список валют
    currencies = await get_all_currencies(db)
    if not currencies:
        raise HTTPException(status_code=400, detail="Валюты в базе не найдены")

    # Создаем мапу код → id
    code_to_id = {c.code: c.id for c in currencies}
    codes = list(code_to_id.keys())

    # Запрашиваем курсы с API
    data = await fetch_exchange_rates(API_KEY)

    if "rates" not in data or "base" not in data:
        raise HTTPException(status_code=502, detail="Ошибка внешнего API: неверный формат ответа")

    base_code = data["base"]

    if base_code not in code_to_id:
        new_currency = Currency(code=base_code)
        db.add(new_currency)
        await db.commit()
        await db.refresh(new_currency)
        code_to_id[base_code] = new_currency.id
        codes.append(base_code)

    base_currency_id = code_to_id[base_code]

    rates = {
        code: rate for code, rate in data["rates"].items()
        if code in code_to_id and code != base_code
    }

    await update_rates(
        session=db,
        base_currency_id=base_currency_id,
        rates_dict=rates,
        code_to_id=code_to_id
    )

    return {
        "detail": f"Курсы валют относительно {base_code} успешно обновлены",
        "updated_rates_count": len(rates)
    }
