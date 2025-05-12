"""Strategy implementations - signal generation logic"""
from .base_strategy import BaseStrategy, StrategyConfig
from .rsi_strategy import RSIStrategy

__all__ = [
    'BaseStrategy',
    'StrategyConfig',
    'RSIStrategy'
]

# Optional strategy registry
STRATEGY_CLASSES = {
    'rsi': RSIStrategy,
    # Add new strategies here as you create them
}

def get_strategy(name: str):
    """Factory method for strategies"""
    return STRATEGY_CLASSES.get(name.lower())