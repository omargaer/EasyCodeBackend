from sqlalchemy.future import select
from .models import Currency, ExchangeRate
from datetime import date, datetime

async def get_all_currencies(session):
    result = await session.execute(select(Currency))
    return result.scalars().all()

async def update_rates(session, base_currency_id, rates_dict, code_to_id):
    now = int(datetime.now().timestamp())
    today = date.today()

    for code, value in rates_dict.items():
        target_currency_id = code_to_id[code]

        # Проверяем: есть ли уже курс на сегодня для этой валютной пары
        stmt = select(ExchangeRate).where(
            ExchangeRate.base_currency_id == base_currency_id,
            ExchangeRate.target_currency_id == target_currency_id,
            ExchangeRate.date == today
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующую запись
            existing.rate_value = value
            existing.timestamp = now
        else:
            # Вставляем новую
            session.add(ExchangeRate(
                base_currency_id=base_currency_id,
                target_currency_id=target_currency_id,
                rate_value=value,
                date=today,
                timestamp=now
            ))

    await session.commit()
