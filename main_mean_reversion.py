# backtest_rig/main_mean_reversion.py
import pandas as pd
import time
from core.data_fetcher import DataFetcher
from core.trade_simulator import TradeSimulator
from strategies.mean_reversion_strategy import MeanReversionStrategy, StrategyConfig
from utils.logger import setup_logging
from utils.dashboard import create_dashboard

def run_mean_reversion_backtest():
    # Start timing
    start_time = time.time()
    
    fetcher = DataFetcher("tAj9_5sMUEaQt0Y_m5fYkfF24dzMsSUp")
    simulator = TradeSimulator()
    
    strategy = MeanReversionStrategy(
        threshold_pct=0.5,  # Trigger trades on 0.5% moves
        max_position_weight=0.3,  # Maximum 30% of capital per position
        sensitivity=2.0,  # Exponential scaling factor
        max_positions=5,  # Allow up to 5 concurrent positions
        config=StrategyConfig(initial_balance=10000)
    )
    
    # Fetch one year of data
    data = fetcher.get_historical_data("PLTR", "2023-01-01")
    
    # Generate signals
    signals = strategy.generate_signals(data)

    # Print trade analysis
    print("\nTrade Analysis:")
    trade_signals = signals[signals['signal'] != 0]
    print("\nSignificant Price Moves and Position Sizes:")
    analysis = pd.DataFrame({
        'Price': data['close'],
        'Daily Return': data['close'].pct_change(),
        'Signal': signals['signal'],
        'Position Weight': signals['trade_weight'],
        'Active Positions': signals['active_positions']
    })
    significant_moves = analysis[analysis['Signal'] != 0]
    print(significant_moves[['Daily Return', 'Signal', 'Position Weight', 'Active Positions']])

    # Run simulation
    results = simulator.run(signals, data)
    
    # Create dashboard
    create_dashboard(data, signals, results['trades'], results['metrics'])
    
    runtime = time.time() - start_time
    
    # Print results
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
    results = run_mean_reversion_backtest() 
