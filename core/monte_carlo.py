# backtest_rig/core/monte_carlo.py
import numpy as np
import pandas as pd
from typing import Dict
from .trade_simulator import TradeSimulator

class MonteCarloSimulator:
    """
    Generates price paths using Geometric Brownian Motion and runs trading simulations
    on each path to evaluate strategy performance.
    """
    def __init__(self, initial_price: float, mu: float, sigma: float):
        """
        Initialize the Monte Carlo simulator
        
        Parameters:
        - initial_price: Starting stock price
        - mu: Expected annual return (drift)
        - sigma: Annual volatility
        """
        self.initial_price = initial_price
        self.mu = mu
        self.sigma = sigma
    
    def generate_price_paths(self, num_paths: int, num_days: int) -> np.ndarray:
        """
        Generate multiple price paths using GBM
        
        Parameters:
        - num_paths: Number of paths to generate
        - num_days: Number of days in each path
        
        Returns:
        - 3D array of shape (num_paths, num_days, 5) with OHLCV data
        """
        # Daily parameters
        dt = 1/252  # Assuming 252 trading days in a year
        drift = (self.mu - 0.5 * self.sigma**2) * dt
        volatility = self.sigma * np.sqrt(dt)
        
        # Generate random shocks
        shocks = np.random.normal(drift, volatility, size=(num_paths, num_days-1))
        
        # Compute price paths
        price_paths = np.zeros((num_paths, num_days))
        price_paths[:, 0] = self.initial_price
        
        for t in range(1, num_days):
            price_paths[:, t] = price_paths[:, t-1] * np.exp(shocks[:, t-1])
        
        # Convert to OHLCV format with some realistic variability
        ohlcv_paths = np.zeros((num_paths, num_days, 5))
        for i in range(num_paths):
            for j in range(num_days):
                # Create realistic OHLC from close price with some randomness
                close = price_paths[i, j]
                high = close * (1 + np.random.uniform(0, 0.01))
                low = close * (1 - np.random.uniform(0, 0.01))
                open_price = close * (1 + np.random.uniform(-0.005, 0.005))
                volume = np.random.randint(100000, 1000000)
                
                ohlcv_paths[i, j] = [open_price, high, low, close, volume]
        
        return ohlcv_paths
    
    def simulate_trading_paths(self, 
                             num_paths: int, 
                             num_days: int,
                             signals: pd.DataFrame,
                             initial_balance: float = 10000.0) -> Dict:
        """
        Run trading simulation on multiple price paths
        
        Parameters:
        - num_paths: Number of Monte Carlo paths to generate
        - num_days: Number of days in each path
        - signals: DataFrame with trading signals (must match num_days)
        - initial_balance: Starting account balance
        
        Returns:
        - Dictionary containing:
            - all_trades: List of trade histories for each path
            - all_metrics: Performance metrics for each path
            - portfolio_paths: Portfolio values over time for each path
        """
        # Generate price paths
        price_paths = self.generate_price_paths(num_paths, num_days)
        
        # Prepare results storage
        all_trades = []
        all_metrics = []
        portfolio_paths = np.zeros((num_paths, num_days))
        
        for i in range(num_paths):
            # Convert path to DataFrame
            path_df = pd.DataFrame(
                price_paths[i], 
                columns=['open', 'high', 'low', 'close', 'volume']
            )
            
            # Create date index
            path_df.index = pd.date_range(
                start=pd.Timestamp.today(), 
                periods=num_days, 
                freq='D'
            )
            
            # Run trading simulation
            simulator = TradeSimulator(initial_balance=initial_balance)
            results = simulator.run(signals=signals, market_data=path_df)
            
            # Store results
            all_trades.append(results['trades'])
            all_metrics.append(results['metrics'])
            
            # Reconstruct portfolio path
            portfolio_path = np.zeros(num_days)
            portfolio_path[0] = initial_balance
            
            # Track portfolio value day by day
            current_balance = initial_balance
            open_positions = []
            
            for j in range(1, num_days):
                # Update positions with current prices
                current_price = path_df.iloc[j]['close']
                positions_value = sum(
                    pos.shares * current_price for pos in open_positions
                )
                portfolio_path[j] = current_balance + positions_value
                
                # Check if any trades occurred on this day
                day_trades = [
                    t for t in results['trades'] 
                    if t.entry_date == path_df.index[j] or t.exit_date == path_df.index[j]
                ]
                
                for trade in day_trades:
                    if trade.entry_date == path_df.index[j]:
                        open_positions.append(trade)
                        current_balance -= trade.shares * trade.entry_price
                    elif trade.exit_date == path_df.index[j]:
                        if trade in open_positions:
                            open_positions.remove(trade)
                        current_balance += trade.shares * trade.exit_price
            
            portfolio_paths[i] = portfolio_path
        
        return {
            'all_trades': all_trades,
            'all_metrics': all_metrics,
            'portfolio_paths': portfolio_paths,
            'price_paths': price_paths
        }