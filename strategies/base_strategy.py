# backtest_rig/strategies/base_strategy.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class StrategyConfig:
    """Base configuration for all strategies"""
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.02  # 2% of balance

class BaseStrategy(ABC):
    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Main strategy logic - must be implemented by child classes
        
        Args:
            data: OHLCV DataFrame with columns:
                  ['open', 'high', 'low', 'close', 'volume']
                  
        Returns:
            DataFrame with:
            - index: Matching input data
            - columns: 
              * 'signal' (-1=SELL, 0=HOLD, 1=BUY)
              * Any additional strategy-specific columns
        """
        pass

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optional helper for indicator calculations"""
        return data