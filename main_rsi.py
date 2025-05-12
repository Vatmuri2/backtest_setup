# backtest_rig/mains/main_rsi.py
import pandas as pd
from core.data_fetcher import DataFetcher
from core.trade_simulator import TradeSimulator
from .strategies.rsi_strategy import RSIStrategy, StrategyConfig

from utils.logger import setup_logging

def run_rsi_backtest():
    # Initialize components
    fetcher = DataFetcher()
    simulator = TradeSimulator()
    
    # Configure strategy
    strategy = RSIStrategy(
        oversold=30,
        overbought=70,
        rsi_period=14,
        config=StrategyConfig(initial_balance=10000)
    )
    
    # Fetch data
    data = fetcher.get_historical_data("AAPL", "2023-01-01")
    
    # Generate signals and execute
    signals = strategy.generate_signals(data)
    results = simulator.run(signals, data)
    
    # Output results
    print(f"\nBacktest Results:")
    print(f"Initial Balance: ${results['metrics']['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['metrics']['final_balance']:,.2f}")
    print(f"Win Rate: {results['metrics']['win_rate']:.1%}")
    
    return results

if __name__ == "__main__":
    setup_logging()
    results = run_rsi_backtest()