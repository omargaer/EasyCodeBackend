# app/main.py
from fastapi import FastAPI
from app.api.v1.routes import rates, getcurrencies, last_update, convert, currencies
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()
app.include_router(rates.router, prefix="/api/v1")
app.include_router(getcurrencies.router, prefix="/api/v1")
app.include_router(last_update.router, prefix="/api/v1")
app.include_router(convert.router, prefix="/api/v1")
app.include_router(currencies.router, prefix="/api/v1")


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")