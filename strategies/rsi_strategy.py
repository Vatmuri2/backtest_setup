# backtest_rig/strategies/rsi_strategy.py
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, StrategyConfig
from typing import Optional

class RSIStrategy(BaseStrategy):
    def __init__(self, 
                 oversold: int = 30,
                 overbought: int = 70,
                 rsi_period: int = 14,
                 config: Optional[StrategyConfig] = None):
        """
        Long-only RSI-based mean reversion strategy
        
        Args:
            oversold: Buy when RSI < this value
            overbought: Sell when RSI > this value
            rsi_period: Lookback window for RSI
        """
        super().__init__(config)
        self.oversold = oversold
        self.overbought = overbought
        self.rsi_period = rsi_period

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        # Initialize signals DataFrame with proper dtypes
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0  # Default to HOLD
        signals['position'] = 0  # Track current position (1 for long, 0 for none)
        signals['rsi'] = np.nan  # Initialize RSI column
        
        # Calculate RSI and generate signals without look-ahead bias
        for i in range(self.rsi_period, len(data)):
            # Get data up to current point only
            current_data = data.iloc[:i+1]
            current_rsi = self._calculate_rsi_for_point(current_data)
            signals.iloc[i, signals.columns.get_loc('rsi')] = current_rsi
            
            # Get previous position
            prev_position = signals['position'].iloc[i-1]
            
            # Generate signals based on current position and RSI
            if prev_position == 0:  # No position
                if current_rsi < self.oversold:
                    signals.iloc[i, signals.columns.get_loc('signal')] = 1  # Buy
                    signals.iloc[i, signals.columns.get_loc('position')] = 1
            elif prev_position == 1:  # Long position
                if current_rsi > self.overbought:
                    signals.iloc[i, signals.columns.get_loc('signal')] = -1  # Sell
                    signals.iloc[i, signals.columns.get_loc('position')] = 0
                else:
                    signals.iloc[i, signals.columns.get_loc('position')] = 1
        
        # Convert signal and position columns to int32 to avoid dtype warnings
        signals['signal'] = signals['signal'].astype('int32')
        signals['position'] = signals['position'].astype('int32')
        
        return signals

    def _calculate_rsi_for_point(self, data: pd.DataFrame) -> float:
        """Calculate RSI for a single point using only past data"""
        if len(data) < self.rsi_period + 1:
            return np.nan
            
        # Calculate price changes
        delta = data['close'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(self.rsi_period).mean().iloc[-1]
        avg_loss = losses.rolling(self.rsi_period).mean().iloc[-1]
        
        # Handle division by zero
        if avg_loss == 0:
            return 100.0
            
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi