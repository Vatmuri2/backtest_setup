# strategies/strategy_template.py
"""
Template for creating new trading strategies

To create a new strategy:
1. Copy this file and rename it (e.g., my_strategy.py)
2. Implement the generate_signals method with your logic
3. Update the class name and docstring
4. Import and use in main.py
"""
import pandas as pd
import numpy as np
from typing import Optional
from .base_strategy import BaseStrategy, StrategyConfig

class TemplateStrategy(BaseStrategy):
    """
    Template strategy - replace with your strategy logic
    
    This is a simple example that you can modify to create your own strategy.
    """
    
    def __init__(self, 
                 param1: float = 1.0,
                 param2: float = 2.0,
                 config: Optional[StrategyConfig] = None):
        """
        Initialize your strategy with parameters
        
        Args:
            param1: Example parameter 1
            param2: Example parameter 2
            config: Strategy configuration
        """
        super().__init__(config)
        self.param1 = param1
        self.param2 = param2
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on your strategy logic
        
        This is where you implement your trading logic. The method should:
        1. Calculate any indicators you need
        2. Determine buy/sell signals
        3. Return a DataFrame with 'signal' and 'trade_weight' columns
        
        Args:
            data: OHLCV DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            DataFrame with columns:
            - 'signal': -1 (SELL), 0 (HOLD), 1 (BUY)
            - 'trade_weight': Position size as fraction of capital (0.0 to 1.0)
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['trade_weight'] = 0.0
        
        # Example: Calculate a simple moving average
        sma_short = data['close'].rolling(window=10).mean()
        sma_long = data['close'].rolling(window=30).mean()
        
        # Example: Generate signals based on moving average crossover
        for i in range(1, len(data)):
            # Buy signal: short MA crosses above long MA
            if sma_short.iloc[i] > sma_long.iloc[i] and sma_short.iloc[i-1] <= sma_long.iloc[i-1]:
                signals.iloc[i, signals.columns.get_loc('signal')] = 1
                signals.iloc[i, signals.columns.get_loc('trade_weight')] = 0.2  # 20% of capital
            
            # Sell signal: short MA crosses below long MA
            elif sma_short.iloc[i] < sma_long.iloc[i] and sma_short.iloc[i-1] >= sma_long.iloc[i-1]:
                signals.iloc[i, signals.columns.get_loc('signal')] = -1
                signals.iloc[i, signals.columns.get_loc('trade_weight')] = 0.2
        
        return signals
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optional: Calculate technical indicators
        
        This is a helper method you can use to calculate indicators
        that you'll use in generate_signals()
        """
        # Example: Add RSI indicator
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        return data

# Example usage in main.py:
"""
from strategies.strategy_template import TemplateStrategy

strategy = TemplateStrategy(
    param1=1.5,
    param2=3.0
)

results = engine.run(
    strategy=strategy,
    symbol="AAPL",
    start_date="2023-01-01",
    backtest_type="standard"
)
"""

