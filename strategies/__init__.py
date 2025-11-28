"""Strategy implementations - signal generation logic"""
from .base_strategy import BaseStrategy, StrategyConfig
from .mean_reversion_strategy import MeanReversionStrategy

__all__ = [
    'BaseStrategy',
    'StrategyConfig',
    'MeanReversionStrategy'
]

# Optional strategy registry
STRATEGY_CLASSES = {
    'mean_reversion': MeanReversionStrategy,
    # Add new strategies here as you create them
}

def get_strategy(name: str):
    """Factory method for strategies"""
    return STRATEGY_CLASSES.get(name.lower())