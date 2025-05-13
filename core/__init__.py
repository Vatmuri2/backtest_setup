"""Core backtesting components - data handling and trade execution"""
from .data_fetcher import DataFetcher
from .trade_simulator import TradeSimulator, Trade

__all__ = [
    'DataFetcher',
    'TradeSimulator',
    'Trade'
]

# Version-aware imports
try:
    from importlib.metadata import version
    __version__ = version("backtest_rig")
except ImportError:
    __version__ = "0.1.0"  # Fallback version