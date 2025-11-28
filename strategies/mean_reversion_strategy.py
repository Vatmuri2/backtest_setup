# backtest_rig/strategies/mean_reversion_strategy.py
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from .base_strategy import BaseStrategy

@dataclass
class StrategyConfig:
    """Configuration for mean reversion strategy"""
    initial_balance: float = 10000.0
    commission_rate: float = 0.001  # 0.1% commission per trade

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, 
                 threshold_pct: float = 0.5,  # Minimum % change to trigger trade
                 max_position_weight: float = 0.3,  # Maximum position size as % of capital
                 sensitivity: float = 2.0,  # Exponential scaling factor
                 max_positions: int = 5,  # Maximum number of concurrent positions
                 config: Optional[StrategyConfig] = None):
        """
        Mean Reversion strategy based on daily price changes
        
        Args:
            threshold_pct: Minimum price change % to trigger trade
            max_position_weight: Maximum position size as fraction of capital
            sensitivity: Controls how quickly position size grows with price change
            max_positions: Maximum number of concurrent positions allowed
            config: Strategy configuration parameters
        """
        self.threshold = threshold_pct / 100  # Convert to decimal
        self.max_position_weight = max_position_weight
        self.sensitivity = sensitivity
        self.max_positions = max_positions
        self.config = config if config is not None else StrategyConfig()

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on price changes"""
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['trade_weight'] = 0.0
        signals['active_positions'] = 0
        
        # Calculate daily returns
        daily_returns = data['close'].pct_change()
        
        for i in range(1, len(data)):
            # Update active positions count
            if i > 0:
                signals.iloc[i, signals.columns.get_loc('active_positions')] = signals.iloc[i-1]['active_positions']
            
            daily_return = daily_returns.iloc[i]
            
            # Skip if return is too small
            if abs(daily_return) < self.threshold:
                continue
                
            # Calculate position weight using exponential scaling
            base_weight = min(abs(daily_return) / self.threshold, 3)  # Cap at 3x threshold
            position_weight = min(
                self.max_position_weight * (base_weight ** self.sensitivity),
                self.max_position_weight
            )
            
            current_positions = signals.iloc[i]['active_positions']
            
            # Buy signal - price dropped more than threshold
            if daily_return < -self.threshold and current_positions < self.max_positions:
                signals.iloc[i, signals.columns.get_loc('signal')] = 1
                signals.iloc[i, signals.columns.get_loc('trade_weight')] = position_weight
                signals.iloc[i, signals.columns.get_loc('active_positions')] = current_positions + 1
                
            # Sell signal - price rose more than threshold
            elif daily_return > self.threshold and current_positions > 0:
                signals.iloc[i, signals.columns.get_loc('signal')] = -1
                signals.iloc[i, signals.columns.get_loc('trade_weight')] = position_weight
                signals.iloc[i, signals.columns.get_loc('active_positions')] = current_positions - 1
        
        return signals