import aiohttp
import asyncio
import csv
from typing import List, Dict

from logger import logger
from config import (
    DELAY_BETWEEN_REQUESTS, BASE_URL,
    CATEGORY_BY_CITY, CITIES, STORE_IDS, REQUIRED_COLUMNS,
    CSV_ENCODING, CSV_NEWLINE, BRAND_ATTRIBUTE_ALIAS,
    BRAND_ATTRIBUTE_NAME, MIN_BRAND_LENGTH, API_HEADERS, PRODUCTS_PER_STORE
)

class CSVWriter:
    """Класс для записи данных в CSV файл"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.fieldnames = REQUIRED_COLUMNS
        self.encoding = CSV_ENCODING
        self.newline = CSV_NEWLINE

    async def write_products(self, products: List[Dict]) -> None:
        """Асинхронная запись списка товаров в CSV файл"""
        def write_to_csv():
            logger.info(f"Начинаем запись {len(products)} товаров в файл {self.filename}")
            with open(self.filename, "w", newline=self.newline, encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                # Записываем только первые 100 товаров
                writer.writerows(products[:100])
                logger.info(f"Записано {len(products[:100])} строк данных в файл {self.filename}")
        
        await asyncio.to_thread(write_to_csv) # Запускает обычную (синхронную) функцию в отдельном потоке как если бы она была async.
        logger.info(f"Сохранили {len(products[:100])} товаров в {self.filename}")

class LentaAPI:
    def __init__(self, city: str):
        self.city = city
        self.headers = API_HEADERS
        self.session = None

    async def __aenter__(self):
        """Создание сессии для запросов к API
        Открывает сессию для запросов к API
        Устанавливает нужные заголовки
        """
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

    def _extract_brand(self, item: Dict) -> str:
        """Извлечение бренда из атрибутов или названия товара"""
        # Сначала ищем в атрибутах
        for attr in item.get("attributes", []):
            if attr.get("alias") == BRAND_ATTRIBUTE_ALIAS or attr.get("name") == BRAND_ATTRIBUTE_NAME:
                return attr.get("value", "")
        
        # Если не нашли в атрибутах, ищем в названии
        name_parts = item.get("name", "").split()
        brand_parts = []
        
        #экспериментальный алгоритм, который быстрее, чем запросы к API
        for i, part in enumerate(name_parts):
            if part.isupper() and len(part) > MIN_BRAND_LENGTH:
                brand_parts.append(part)
                # Проверяем следующие слова
                j = i + 1
                while j < len(name_parts) and name_parts[j].isupper() and len(name_parts[j]) > MIN_BRAND_LENGTH:
                    brand_parts.append(name_parts[j])
                    j += 1
                break
        
        return " ".join(brand_parts)

    def get_store(self) -> Dict:
        """Создание объекта магазина из конфигурации"""
        store_id = STORE_IDS[self.city]
        region_id = CITIES[self.city]
        
        store = {
            "id": store_id,
            "regionId": region_id,
            "title": f"Магазин Лента {self.city} (ID: {store_id})"
        }
        
        logger.info(f"Создан объект магазина: {store['title']}")
        return store

    async def get_products(self, store: Dict, category_id: int, total_needed: int = 20) -> List[Dict]:
        """Получение списка товаров"""
        if not store:
            logger.error(f"Нет информации о магазине для города {self.city}")
            return []
            
        logger.info(f"Получение товаров для магазина {store['id']} ({store['title']}) в городе {self.city}")
        url = f"{BASE_URL}/catalog/items"
        collected = []
        offset = 0

        while len(collected) < total_needed:
            current_limit = min(PRODUCTS_PER_STORE, total_needed - len(collected))
            logger.info(f"Запрашиваем {current_limit} товаров, текущее количество: {len(collected)}")
            
            payload = {
                "categoryId": category_id,
                "limit": current_limit,
                "offset": offset,
                "sort": {"order": "desc", "type": "popular"},
                "regionId": store["regionId"],
                "pickupStoreId": store["id"],
                "showOutOfStock": False,
                "filters": {
                    "multicheckbox": [{"key": "region", "values": [str(store["regionId"])]}]
                }
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Ошибка {response.status} при получении товаров для магазина {store['id']}")
                    return []
                    
                data = await response.json()
                items = data.get("items", [])
                
                if not items:
                    logger.info("Больше товаров нет")
                    break

                logger.info(f"Получено {len(items)} товаров в текущем запросе")
                # Добавляем только нужное количество товаров
                remaining = total_needed - len(collected)
                items_to_add = items[:remaining]
                collected.extend(items_to_add)
                
                if len(collected) >= total_needed:
                    break
                    
                offset += len(items)
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

        # Дополнительная проверка на точное количество
        collected = collected[:total_needed]
        logger.info(f"Итоговое количество собранных товаров: {len(collected)}")

        formatted_products = [
            {
                'id': item["id"],
                'name': item.get("name", ""),
                'regular_price': item["prices"]["priceRegular"]/100,
                'promo_price': item["prices"]["price"]/100,
                'brand': self._extract_brand(item)
            }
            for item in collected
        ]
        
        logger.info(f"Количество отформатированных товаров: {len(formatted_products)}")
        return formatted_products

async def main():
    """Основная функция"""
    for city in CITIES:
        try: # что бы прога не упала, ошибка залогируеться а цыкл пойдёт дальше
            async with LentaAPI(city) as api:
                store = api.get_store()
                products = await api.get_products(store, CATEGORY_BY_CITY[city], total_needed=PRODUCTS_PER_STORE)
                
                # Используем CSVWriter для сохранения данных
                writer = CSVWriter(f"lenta_{city.lower().replace(' ', '_')}.csv")
                await writer.write_products(products)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке города {city}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
