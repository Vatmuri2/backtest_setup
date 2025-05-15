import pandas as pd
import numpy as np
from typing import Union

class TechnicalIndicators:
    """
    A collection of technical indicators used in trading strategies.
    All methods are static and can be called directly from the class.
    """
    
    @staticmethod
    def calculate_CCI(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate the Commodity Channel Index (CCI)
        
        Args:
            data: DataFrame with 'high', 'low', and 'close' columns
            period: The period over which to calculate CCI
            
        Returns:
            pd.Series: CCI values
        """
        # Calculate True Price (TP)
        TP = (data['high'] + data['low'] + data['close']) / 3
        
        # Calculate Simple Moving Average (SMA)
        SMA = TP.rolling(window=period).mean()
        
        # Calculate Mean Deviation
        mean_dev = TP.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
        
        # Calculate CCI
        CCI = (TP - SMA) / (0.015 * mean_dev)
        
        return CCI

    @staticmethod
    def calculate_OBV(data: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV)
        
        Args:
            data: DataFrame with 'close' and 'volume' columns
            
        Returns:
            pd.Series: OBV values
        """
        # Initialize OBV with first value
        obv = pd.Series(0, index=data.index)
        
        # Calculate OBV
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
            elif data['close'].iloc[i] < data['close'].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv

    @staticmethod
    def calculate_ATR(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        Args:
            data: DataFrame with 'high', 'low', and 'close' columns
            period: The period over which to calculate ATR
            
        Returns:
            pd.Series: ATR values
        """
        # Calculate True Range components
        TR_components = pd.concat([
            data['high'] - data['low'],
            abs(data['high'] - data['close'].shift(1)),
            abs(data['low'] - data['close'].shift(1))
        ], axis=1)

        # Calculate True Range and ATR
        TR = TR_components.max(axis=1)
        ATR = TR.rolling(window=period).mean()
        
        return ATR
    
'''
    def calculate_CCI(self, data: pd.DataFrame) -> pd.Series: 
        
        #Calculate True Price (TP)
        TP = (data.iloc[:, data.columns.get_loc('high')] + 
              data.iloc[:, data.columns.get_loc('low')] + 
              data.iloc[:, data.columns.get_loc('close')]) / 3
        #Calculate Simple Moving Average (SMA)
        SMA = TP.rolling(window=self.CCI_period).mean()
        #Calculate Mean Deviation
        #Mean Deviation is the average of the absolute differences between TP and SMA
        mean_dev = TP.rolling(window=self.CCI_period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
        CCI = (TP - SMA) / (0.015 * mean_dev)

        return CCI

    def calculate_OBV(self, data: pd.DataFrame) -> pd.Series:
        obv = [0]

        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i - 1]:
                obv.append(obv[-1] + data['volume'][i])
            elif data['close'].iloc[i] < data['close'].iloc[i - 1]:
                obv.append(obv[-1] - data['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        obv = pd.Series(obv, index=data.index, name='OBV')

    def calculate_ATR(self, data: pd.DataFrame) -> pd.Series:
        pass
        # Calculate the ATR using the given parameters
        TR_components = pd.concat([
            data['high'] - data['low'],
            abs(data['high'] - data['close'].shift(1)),
            abs(data['low'] - data['close'].shift(1))
        ], axis=1)

        TR = TR_components.max(axis=1)
        atr = TR.rolling(window=self.ATR_period).mean()
        return atr
    '''