# main.py
"""
Streamlined Backtesting Rig
Simple interface for running backtests with any strategy

To create your own strategy:
1. Copy strategies/strategy_template.py to strategies/my_strategy.py
2. Implement your trading logic
3. Import and use it here!
"""
from core.backtest_engine import BacktestEngine
from strategies.mean_reversion_strategy import MeanReversionStrategy, StrategyConfig
from utils.logger import setup_logging

def main():
    """Main entry point for backtesting"""
    # Setup logging
    setup_logging()
    
    # ============================================
    # STEP 1: Initialize backtest engine
    # ============================================
    engine = BacktestEngine(
        api_key="tAj9_5sMUEaQt0Y_m5fYkfF24dzMsSUp",  # Can also use env var POLYGON_API_KEY
        initial_balance=10000.0
    )
    
    # ============================================
    # STEP 2: Create your strategy
    # ============================================
    # Example: Mean Reversion Strategy
    strategy = MeanReversionStrategy(
        threshold_pct=0.5,          # Trigger trades on 0.5% moves
        max_position_weight=0.3,     # Max 30% of capital per position
        sensitivity=2.0,             # Exponential scaling factor
        max_positions=5,             # Max concurrent positions
        config=StrategyConfig(initial_balance=10000)
    )
    
    # To use your own strategy:
    # from strategies.my_strategy import MyStrategy
    # strategy = MyStrategy(param1=1.0, param2=2.0)
    
    # ============================================
    # STEP 3: Run backtest
    # ============================================
    results = engine.run(
        strategy=strategy,
        symbol="TQQQ",                    # Stock ticker
        start_date="2023-01-01",          # Start date
        backtest_type="standard",         # "standard" or "monte_carlo"
        num_simulations=100,              # Only used for monte_carlo
        show_dashboard=True               # Opens dashboard in browser automatically
    )
    
    return results

if __name__ == "__main__":
    main()

