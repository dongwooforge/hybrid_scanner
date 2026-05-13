# utils/config.py

import os
from pathlib import Path

class Config:
    # 1. 시장 모드 설정
    MARKET_MODE = os.getenv("MARKET_MODE", "KR").upper() #KR 또는 US 모드

    # 2. 기본 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    STORAGE_DIR = BASE_DIR / "storage" / MARKET_MODE
    
    # 3. 시장별 특화 설정
    SETTINGS = {
        "KR": {
            "DATA_DIR": STORAGE_DIR / "raw_data",
            "REPORT_DIR": STORAGE_DIR / "reports",
            "TICKER_FILE": STORAGE_DIR / "ticker_list.txt",
            "INTERVAL": "1d",
            "CURRENCY": "KRW",
            "SUFFIX": [".KS", ".KQ"]
        },
        "US": {
            "DATA_DIR": STORAGE_DIR / "raw_data",
            "REPORT_DIR": STORAGE_DIR / "reports",
            "TICKER_FILE": STORAGE_DIR / "ticker_list.txt",
            "INTERVAL": "4h",
            "CURRENCY": "USD",
            "SUFFIX": [""]
        }
    }

    @classmethod
    def get(cls, key):
        return cls.SETTINGS[cls.MARKET_MODE].get(key)

    @classmethod
    def get_path(cls, key):
        path = cls.get(key)
        if path and isinstance(path, Path) and not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path