# backtest_rig/mains/main_rsi.py
import pandas as pd
import time
from core.data_fetcher import DataFetcher
from core.trade_simulator import TradeSimulator
from strategies.CCI_OBV_ATR_strategy import CciObvAtrStrategy, StrategyConfig
from utils.logger import setup_logging
from utils.dashboard import create_dashboard

def run_CCI_OBV_ATR_backtest():
    # Start timing
    start_time = time.time()
    
    # Initialize components
    fetcher = DataFetcher("tAj9_5sMUEaQt0Y_m5fYkfF24dzMsSUp")
    simulator = TradeSimulator()
    
    # Configure strategy
    strategy = CciObvAtrStrategy(
        CCI_threshold = 100,
        CCI_period = 20,
        ATR_period = 14,
        config=StrategyConfig(initial_balance=10000)
    )
    
    # Fetch data
    data = fetcher.get_historical_data("NVDL", "2023-01-01")
    
    # Generate signals and execute
    signals = strategy.generate_signals(data)
    results = simulator.run(signals, data)
    
    # Create dashboard
    create_dashboard(data, signals, results['trades'], results['metrics'])
    
    # Calculate runtime
    runtime = time.time() - start_time
    
    # Output results
    print(f"\nBacktest Results:")
    print(f"Initial Balance: ${results['metrics']['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['metrics']['final_balance']:,.2f}")
    print(f"Win Rate: {results['metrics']['win_rate']:.1%}")
    print(f"Runtime: {runtime:.2f} seconds")
    print(f"\nDashboard saved to: outputs/dashboard.html")
    
    return results

if __name__ == "__main__":
    setup_logging()
    results = run_CCI_OBV_ATR_backtest()