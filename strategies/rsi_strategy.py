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
                 max_positions: int = 5,  # Maximum number of concurrent positions
                 position_size: float = 0.1,  # Base position size as fraction of capital
                 config: Optional[StrategyConfig] = None):
        """
        Long-only RSI-based mean reversion strategy
        
        Args:
            oversold: Buy when RSI < this value
            overbought: Sell when RSI > this value
            rsi_period: Lookback window for RSI
            max_positions: Maximum number of concurrent positions allowed
            position_size: Base position size as fraction of total capital
        """
        super().__init__(config)
        self.oversold = oversold
        self.overbought = overbought
        self.rsi_period = rsi_period
        self.max_positions = max_positions
        self.position_size = position_size

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        print(">>> generate_signals() with trade_weight column is running...")  # Debug: Ensure correct file is used
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['position'] = 0
        signals['rsi'] = np.nan
        signals['trade_weight'] = 0.0  # Indicates strength of the signal
        signals['active_positions'] = 0  # Track number of active positions

        for i in range(self.rsi_period, len(data)):
            current_data = data.iloc[:i+1]
            current_rsi = self._calculate_rsi_for_point(current_data)
            signals.iloc[i, signals.columns.get_loc('rsi')] = current_rsi
            
            # Update active positions count
            if i > 0:
                signals.iloc[i, signals.columns.get_loc('active_positions')] = signals.iloc[i-1]['active_positions']
            
            # Buy logic
            if current_rsi < self.oversold and signals.iloc[i]['active_positions'] < self.max_positions:
                # Calculate signal strength (0 to 1)
                signal_strength = (self.oversold - current_rsi) / self.oversold
                
                # Only take trade if signal is strong enough
                if signal_strength > 0.2:  # Minimum threshold
                    signals.iloc[i, signals.columns.get_loc('signal')] = 1
                    signals.iloc[i, signals.columns.get_loc('trade_weight')] = (
                        self.position_size * signal_strength
                    )
                    signals.iloc[i, signals.columns.get_loc('active_positions')] += 1

            # Sell logic - check each position
            elif current_rsi > self.overbought and signals.iloc[i]['active_positions'] > 0:
                signal_strength = (current_rsi - self.overbought) / (100 - self.overbought)
                if signal_strength > 0.2:  # Minimum threshold
                    signals.iloc[i, signals.columns.get_loc('signal')] = -1
                    signals.iloc[i, signals.columns.get_loc('trade_weight')] = signal_strength
                    signals.iloc[i, signals.columns.get_loc('active_positions')] -= 1

        signals['signal'] = signals['signal'].astype('int32')
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