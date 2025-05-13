# backtest_rig/mains/main_rsi.py
import pandas as pd
import time
from core.data_fetcher import DataFetcher
from core.trade_simulator import TradeSimulator
from strategies.rsi_strategy import RSIStrategy, StrategyConfig
from utils.logger import setup_logging
from utils.dashboard import create_dashboard

def run_rsi_backtest():
    # Start timing
    start_time = time.time()
    
    fetcher = DataFetcher("tAj9_5sMUEaQt0Y_m5fYkfF24dzMsSUp")
    simulator = TradeSimulator()
    
    strategy = RSIStrategy(
        oversold=30,
        overbought=70,
        rsi_period=14,
        max_positions=5,  # Allow up to 5 concurrent positions
        position_size=0.1,  # Use 10% of capital per position
        config=StrategyConfig(initial_balance=10000)
    )
    
    data = fetcher.get_historical_data("PLTR", "2023-01-01")
    
    # Generate signals
    signals = strategy.generate_signals(data)

    # Print active positions and trade weights for non-zero signals
    print("\nTrade Analysis:")
    trade_signals = signals[signals['signal'] != 0]
    print(trade_signals[['rsi', 'signal', 'trade_weight', 'active_positions']])

    results = simulator.run(signals, data)
    
    create_dashboard(data, signals, results['trades'], results['metrics'])
    
    runtime = time.time() - start_time
    
    print(f"\nBacktest Results:")
    print(f"Initial Balance: ${results['metrics']['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['metrics']['final_balance']:,.2f}")
    print(f"Total Return: {((results['metrics']['final_balance'] / results['metrics']['initial_balance']) - 1):.1%}")
    print(f"Win Rate: {results['metrics']['win_rate']:.1%}")
    print(f"Total Trades: {results['metrics']['total_trades']}")
    print(f"Profit Factor: {results['metrics']['profit_factor']:.2f}")
    print(f"Max Drawdown: {results['metrics']['max_drawdown']:.1%}")
    print(f"Runtime: {runtime:.2f} seconds")
    print(f"\nDashboard saved to: outputs/dashboard.html")
    
    return results

if __name__ == "__main__":
    setup_logging()
    results = run_rsi_backtest()