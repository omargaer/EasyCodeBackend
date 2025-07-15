from sqlalchemy import Column, Integer, String, Numeric, Date, BigInteger, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Currency(Base):
    __tablename__ = 'currencies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(64))

    base_rates = relationship("ExchangeRate", back_populates="base_currency", foreign_keys='ExchangeRate.base_currency_id')
    target_rates = relationship("ExchangeRate", back_populates="target_currency", foreign_keys='ExchangeRate.target_currency_id')

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    base_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    target_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate_value = Column(Numeric(20, 8), nullable=False)
    date = Column(Date, nullable=False)
    timestamp = Column(BigInteger, nullable=False)

    base_currency = relationship("Currency", foreign_keys=[base_currency_id], back_populates='base_rates')
    target_currency = relationship("Currency", foreign_keys=[target_currency_id], back_populates='target_rates')
