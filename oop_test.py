import requests
import pandas as pd
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import concurrent.futures
from functools import wraps
import os

# Константы
MAX_WORKERS = 2  # Максимальное количество потоков
DEFAULT_TIMEOUT = 10  # Таймаут для запросов в секундах
DEFAULT_CATEGORY_ID = 4  # ID категории по умолчанию
DEFAULT_LIMIT = 2 # Лимит товаров по умолчанию
DEFAULT_FILENAME = "lenta_products.csv"  # Имя файла по умолчанию
REQUIRED_COLUMNS = ['id', 'name', 'regular_price', 'promo_price', 'brand']  # Обязательные колонки
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'  # Формат логов
LOG_FILE = 'lenta_parser.log'  # Файл для логов

class LoggerSingleton:
    """Синглтон для логирования"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """Инициализация логгера"""
        self.logger = logging.getLogger('LentaParser')
        self.logger.setLevel(logging.INFO)
        
        # Форматтер для логов
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Хендлер для файла с явным указанием кодировки UTF-8
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Получение логгера"""
        return self.logger

# Инициализация логгера
logger = LoggerSingleton().get_logger()

def timer_decorator(func):
    """Декоратор для измерения времени выполнения функции"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Функция {func.__name__} выполнилась за {execution_time:.2f} секунд")
        return result
    return wrapper

@dataclass
class Product:
    """Модель товара"""
    id: Optional[int]
    name: str
    regular_price: float
    promo_price: float
    brand: str

class LentaAPI:
    """Класс для работы с API Ленты"""
    
    def __init__(self):
        self.base_url = "https://api.lenta.com/v1/catalog"
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": "ru-RU;q=1.0",
            "Content-Type": "application/json",
            "User-Agent": "Lenta/6.42.0 (iPhone; iOS 17.1; Scale/3.00)",
            "X-Device-Brand": "iPhone",
            "X-Device-OS": "iOS",
            "X-Device-OS-Version": "17.1",
            "X-Device-Name": "iPhone14,2",
            "X-Platform": "omniapp",
            "X-Retail-Brand": "lo",
            "X-Delivery-Mode": "pickup",
            "Client": "ios_17.1_6.42.0",
            "App-Version": "6.42.0",
            "DeviceId": "9D41527E-77C3-4168-8CB7-6FBE74A0D64F",
            "X-Device-id": "9D41527E-77C3-4168-8CB7-6FBE74A0D64F",
            "AdvertisingId": "CBB9CEB8-2E25-474D-A7A7-9B19EBCB75CA",
            "Adid": "2eae1cfe0ba94d0b45bffe0906e8817d",
            "MarketingPartnerKey": "mp403-3a8bc38112eecfff5936dc001481afe3",
            "Qrator-Token": "81bad713eee23da5bb253934ab1f7da5",
            "SessionToken": "7AA98197772E858136AD3D73C23FFE6C",
            "AuthToken": "7AA98197772E858136AD3D73C23FFE6C",
            "PassportAccessToken": "eyJraWQiOiJkVkR2eTBPUmg5bzB4UHhxdnh4SmE0UnlBME1tVVlnSDExdzdQa0diWTlVIiwiYWxnIjoiUlMyNTYiLCJ0eXAiOiJKV1QifQ....",
            "Connection": "keep-alive",
            "Timestamp": str(int(time.time())),
            "Created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "LocalTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "RequestId": "71jral78dvlwiqzutwlmcdu1osuc3i5v",
            "Method": "catalogItemsListing",
            "Experiments": "exp_accrual_history.test,exp_another_button_ch.test_A,...",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_products(self, category_id: int = DEFAULT_CATEGORY_ID, limit: int = DEFAULT_LIMIT) -> List[Dict]:
        """Получение списка товаров"""
        try:
            json_data = {
                "categoryId": category_id,
                "sort": {
                    "order": "desc",
                    "type": "popular"
                },
                "limit": limit,
            }
            
            response = self.session.post(f"{self.base_url}/items", json=json_data, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка товаров: {str(e)}")
            return []

    def get_product_details(self, product_id: int) -> Optional[Dict]:
        """Получение детальной информации о товаре"""
        try:
            response = self.session.get(f"{self.base_url}/items/{product_id}", timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при получении деталей товара {product_id}: {str(e)}")
            return None

class ProductParser:
    """Класс для парсинга товаров по id"""
    
    def __init__(self, api: LentaAPI):
        self.api = api

    def extract_brand(self, item_detail: Optional[Dict]) -> Optional[str]:
        """Извлечение бренда из атрибутов товара"""
        if not item_detail:
            return None
            
        for attr in item_detail.get("attributes", []):
            if attr.get("alias") == "brand" or attr.get("name") == "Бренд":
                return attr.get("value")
        return None

    def parse_product(self, product_data: Dict) -> Optional[Product]:
        """Парсинг данных товара"""
        try:
            # Получаем цены
            prices = product_data.get('prices', {})
            
            # Преобразуем цены из копеек в рубли
            regular_price = prices.get('priceRegular')
            if regular_price is not None:
                regular_price = regular_price / 100
                
            promo_price = prices.get('price')
            if promo_price is not None:
                promo_price = promo_price / 100
            
            # Получаем детальную информацию о товаре
            product_id = product_data.get('id')
            if not product_id:
                logger.error("Ошибка: отсутствует ID товара")
                return None
                
            item_detail = self.api.get_product_details(product_id)
            
            # Получаем бренд из детальной информации
            brand = self.extract_brand(item_detail)
            
            return Product(
                id=product_id,
                name=product_data.get("name", ""),
                regular_price=regular_price or 0.0,
                promo_price=promo_price or 0.0,
                brand=brand or ""
            )
        except Exception as e:
            logger.error(f"Ошибка при парсинге товара: {str(e)}")
            return None

class DataSaver:
    """Класс для сохранения данных"""
    
    def __init__(self, filename: str = DEFAULT_FILENAME):
        self.filename = filename

    @timer_decorator
    def save_products(self, products: List[Product]) -> None:
        """Сохранение товаров в CSV"""
        try:
            df = pd.DataFrame([vars(p) for p in products])
            df[REQUIRED_COLUMNS].to_csv(self.filename, index=False, encoding='utf-8')
            logger.info(f"Данные успешно сохранены в {self.filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в CSV: {str(e)}")

@timer_decorator
def process_products_parallel(products: List[Dict], parser: ProductParser, max_workers: int = MAX_WORKERS) -> List[Product]:
    """Параллельная обработка товаров"""
    logger.info(f"Начинаем параллельную обработку {len(products)} товаров с {max_workers} потоками")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Создаем задачи для каждого товара
        future_to_product = {
            executor.submit(parser.parse_product, product): product 
            for product in products
        }
        
        results = []
        completed = 0
        
        # Собираем результаты по мере их готовности
        for future in concurrent.futures.as_completed(future_to_product):
            try:
                result = future.result()
                if result:
                    results.append(result)
                completed += 1
                if completed % 10 == 0:  # Логируем каждые 10 товаров
                    logger.info(f"Обработано {completed}/{len(products)} товаров")
            except Exception as e:
                logger.error(f"Ошибка при обработке товара: {str(e)}")
                
    logger.info(f"Завершена обработка {len(results)} товаров")
    return results

@timer_decorator
def main():
    """Основная функция"""
    start_time = time.time()
    
    # Инициализация компонентов
    api = LentaAPI()
    parser = ProductParser(api)
    
    # Получение товаров
    products = api.get_products()
    
    if products:
        logger.info(f"Получено {len(products)} товаров")
        
        # Парсим товары параллельно
        parsed_products = process_products_parallel(products, parser)
        
        # Сохраняем в CSV
        saver = DataSaver()
        saver.save_products(parsed_products)
        
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Всего собрано товаров: {len(parsed_products)}")
        logger.info(f"Общее время выполнения: {total_time:.2f} секунд")
    else:
        logger.error("Не удалось получить товары")

if __name__ == "__main__":
    main()
