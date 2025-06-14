# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Константы для логирования
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO
LOG_NAME = "LentaParser"
LOG_DIR = "logs"

class JSONHandler(logging.Handler):
    """Обработчик для сохранения логов в JSON файл"""
    
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.logs = []
        
        # Создаем директорию для логов если её нет
        Path(LOG_DIR).mkdir(exist_ok=True)
        
    def emit(self, record: logging.LogRecord) -> None:
        """Сохраняет запись лога в JSON формате"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        self.logs.append(log_entry)
        
        # Записываем в файл после каждого логирования
        with open(f"{LOG_DIR}/{self.filename}", 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

class LoggerSingleton:
    """Синглтон для логирования"""
    _instance: Optional['LoggerSingleton'] = None
    
    def __new__(cls) -> 'LoggerSingleton':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self) -> None:
        """Инициализация логгера"""
        self.logger = logging.getLogger(LOG_NAME)
        self.logger.setLevel(LOG_LEVEL)
        
        # Создаем форматтер
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Создаем обработчик для JSON
        json_handler = JSONHandler(f"lenta_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Добавляем обработчики к логгеру
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)
    
    def get_logger(self) -> logging.Logger:
        """Получение экземпляра логгера"""
        return self.logger

# Создаем глобальный экземпляр логгера
logger = LoggerSingleton().get_logger() 