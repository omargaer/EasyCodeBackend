from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Currency

router = APIRouter()

@router.get("/currencies/codes")
async def get_currency_codes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Currency.code))
    codes = result.scalars().all()
    return sorted(codes)
