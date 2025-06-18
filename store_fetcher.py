"""
Простой модуль для получения магазинов Лента
"""
import aiohttp
import asyncio
import csv
from datetime import datetime

from logger import logger
from config import BASE_URL, CITIES, API_HEADERS, CSV_ENCODING, CSV_NEWLINE


async def main():
    all_stores = []
    
    for city in CITIES:
        logger.info(f"Получаем магазины для {city}")
        
        async with aiohttp.ClientSession(headers=API_HEADERS) as session:
            async with session.post(f"{BASE_URL}/stores/pickup/search", json={
                "regionId": CITIES[city],
                "searchQuery": "",
                "limit": 100,
                "page": 1,
                "sort": {"order": "asc", "type": "distance"}
            }) as response:
                stores = (await response.json()).get("items", [])
                
        for store in stores:
            store['city'] = city
            
        all_stores.extend(stores)
        logger.info(f"Получено {len(stores)} магазинов для {city}")
    
    filename = f"lenta_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline=CSV_NEWLINE, encoding=CSV_ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'city'])
        writer.writeheader()
        writer.writerows([{'id': s['id'], 'title': s['title'], 'city': s['city']} for s in all_stores])
    
    logger.info(f"Сохранено {len(all_stores)} магазинов в {filename}")


if __name__ == "__main__":
    asyncio.run(main()) 