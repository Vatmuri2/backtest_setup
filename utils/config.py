# utils/config.py
import os
from pathlib import Path
from typing import Optional

class Config:
    """Central configuration for backtesting"""
    
    def __init__(self):
        # Base directories
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.RESULTS_DIR = self.BASE_DIR / "results"
        
        # API configuration
        self.POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "your_api_key_here")
        
        # Trading configuration
        self.INITIAL_BALANCE = 10000.0
        self.RISK_PER_TRADE = 0.02  # 2% of balance
        
        # Create directories
        self._create_dirs()
    
    def _create_dirs(self):
        """Ensure required directories exist"""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.RESULTS_DIR.mkdir(exist_ok=True)

# Singleton instance
config = Config()