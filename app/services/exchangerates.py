import aiohttp

async def fetch_exchange_rates(api_key: str):
    url = "https://api.exchangeratesapi.io/v1/latest"
    params = {
        "access_key": api_key,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()
