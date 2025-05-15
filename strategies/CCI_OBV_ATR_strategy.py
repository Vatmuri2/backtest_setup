import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, StrategyConfig
from typing import Optional
from .Indicator_generators import TechnicalIndicators

class CciObvAtrStrategy(BaseStrategy):
    """
    CCI + OBV + ATR Strategy
    
    1. ATR (Average True Range) - Volatility
    - Tells you how much an asset typically moves.
    - Helps you size positions or set stop-loss and take-profit levels.
    - Doesn't give direction, but shows market energy.

    2. OBV (On-Balance Volume) - Volume-Driven Momentum
    - Measures cumulative buying/selling pressure.
    - Used to confirm trends: rising OBV = buyers dominate; falling OBV = sellers dominate.
    - Excellent confirmation tool for breakouts.

    3. CCI (Commodity Channel Index) - Trend Strength & Reversal Zones
    - Oscillator that shows how far price deviates from its moving average.
    - Above +100 = strong uptrend; below -100 = strong downtrend.
    - Often used for entry signals or to detect mean reversion.

    4. Strategy Logic
    - CCI gives actionable signals (enter long/short).
    - OBV confirms whether big players are backing the move.
    - ATR protects your trade with dynamic risk control.
    Together, they form a triangle of:
    - Signal (CCI)
    - Validation (OBV)
    - Risk Control (ATR)
    """

    def __init__(self,
             CCI_threshold: int = 100,
             CCI_period: int = 20,
             ATR_period: int = 14,
             ATR_min: float = 1.0, 
             config: Optional[StrategyConfig] = None):
        
        # Initialize values
        super().__init__(config)
        self.CCI_threshold = CCI_threshold
        self.CCI_period = CCI_period
        self.ATR_period = ATR_period
        self.ATR_min = ATR_min


        #self.obv = self.I(OBV, self.data.Close, self.data.Volume)
        #self.atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close, 14)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        # Calculate indicators using the TechnicalIndicators class
        CCI = TechnicalIndicators.calculate_CCI(data, period=self.CCI_period)
        OBV = TechnicalIndicators.calculate_OBV(data)
        ATR = TechnicalIndicators.calculate_ATR(data, period=self.ATR_period)
        
        # Create signals DataFrame
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['position'] = 0
        signals['CCI'] = CCI
        signals['OBV'] = OBV
        signals['ATR'] = ATR

        signal_col = signals.columns.get_loc('signal')
        position_col = signals.columns.get_loc('position')
        CCI_col = signals.columns.get_loc('CCI')
        OBV_col = signals.columns.get_loc('OBV')
        ATR_col = signals.columns.get_loc('ATR')

        for i in range(max(self.CCI_period, self.ATR_period), len(data)):
            #check false values
            if pd.isna(signals.iloc[i, CCI_col]) or pd.isna(signals.iloc[i, OBV_col]) or pd.isna(signals.iloc[i-1, OBV_col]) or pd.isna(signals.iloc[i, ATR_col]):
                continue
            #check if ATR is below the minimum threshold, if so, too volatile and skip the iteration
            if signals.iloc[i, ATR_col] < self.ATR_min:
                continue

            cci_now = signals.iloc[i, CCI_col]
            obv_diff = signals.iloc[i, OBV_col] - signals.iloc[i-1, OBV_col]
            prev_position = signals.iloc[i-1, position_col]

            if prev_position == 0:
                if cci_now > self.CCI_threshold and obv_diff > 0:
                    signals.iloc[i, signal_col] = 1
                    signals.iloc[i, position_col] = 1
            elif prev_position == 1:
                if cci_now < -self.CCI_threshold and obv_diff < 0:
                    signals.iloc[i, signal_col] = -1
                    signals.iloc[i, position_col] = 0
                else:
                    signals.iloc[i, position_col] = 1

        signals['signal'] = signals['signal'].astype('int32')
        signals['position'] = signals['position'].astype('int32')

        return signals
        

