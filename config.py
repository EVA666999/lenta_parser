# -*- coding: utf-8 -*-
from typing import Dict
from datetime import datetime
import time

# Константы для API
DEFAULT_TIMEOUT: int = 10
PAGE_LIMIT: int = 20
DELAY_BETWEEN_REQUESTS: int = 1
BASE_URL: str = "https://api.lenta.com/v1"

# Константы для категорий и городов
CATEGORY_BY_CITY: Dict[str, int] = {
    "Москва": 2,
    "Санкт-Петербург": 2
}

CITIES: Dict[str, int] = {
    'Москва': 1,
    'Санкт-Петербург': 3
}

STORE_IDS: Dict[str, int] = {
    'Москва': 104,
    'Санкт-Петербург': 3135
}

# Константы для CSV
REQUIRED_COLUMNS: list = ['id', 'name', 'regular_price', 'promo_price', 'brand']
CSV_ENCODING: str = 'utf-8'
CSV_NEWLINE: str = ''

# Константы для брендов
BRAND_ATTRIBUTE_ALIAS: str = "brand"
BRAND_ATTRIBUTE_NAME: str = "Бренд"
MIN_BRAND_LENGTH: int = 1

# Константы для заголовков API
API_HEADERS: Dict[str, str] = {
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
    "Experiments": "exp_accrual_history.test,exp_another_button_ch.test_A,..."
}

# Product settings
PRODUCTS_PER_STORE = 100  # Количество товаров для каждого магазина 