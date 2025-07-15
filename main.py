# app/main.py
from fastapi import FastAPI
from app.api.v1.routes import rates, getcurrencies
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.include_router(rates.router, prefix="/api/v1")
app.include_router(getcurrencies.router, prefix="/api/v1")

