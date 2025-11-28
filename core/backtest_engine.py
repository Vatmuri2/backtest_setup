# core/backtest_engine.py
import time
import numpy as np
import pandas as pd
from typing import Dict, Optional, Literal
from .data_fetcher import DataFetcher
from .trade_simulator import TradeSimulator
from .monte_carlo import MonteCarloSimulator
from .metrics import MetricsCalculator
from utils.dashboard import create_dashboard, open_dashboard_server
from utils.monte_carlo_dashboard import MonteCarloDashboard
from utils.logger import setup_logging

class BacktestEngine:
    """
    Streamlined backtesting engine that handles all backtesting operations
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 initial_balance: float = 10000.0,
                 trading_days: int = 252):
        """
        Initialize backtesting engine
        
        Args:
            api_key: Polygon API key (defaults to environment variable)
            initial_balance: Starting capital
            trading_days: Trading days per year for annualization
        """
        self.fetcher = DataFetcher(api_key)
        self.initial_balance = initial_balance
        self.trading_days = trading_days
        self.metrics_calc = MetricsCalculator(initial_balance, trading_days)
        self.logger = setup_logging()
    
    def run(self,
            strategy,
            symbol: str,
            start_date: str,
            end_date: Optional[str] = None,
            backtest_type: Literal["standard", "monte_carlo"] = "standard",
            num_simulations: int = 100,
            show_dashboard: bool = True) -> Dict:
        """
        Run a backtest with a strategy
        
        Args:
            strategy: Strategy instance (must have generate_signals method)
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD, optional)
            backtest_type: "standard" or "monte_carlo"
            num_simulations: Number of Monte Carlo paths (if monte_carlo)
            show_dashboard: Whether to generate and show dashboard
        
        Returns:
            Dictionary with backtest results and metrics
        """
        start_time = time.time()
        
        self.logger.info(f"Starting {backtest_type} backtest for {symbol}")
        
        # Fetch data
        data = self.fetcher.get_historical_data(symbol, start_date, end_date)
        if data.empty:
            raise ValueError(f"No data fetched for {symbol}")
        
        # Generate signals
        signals = strategy.generate_signals(data)
        
        # Run backtest
        if backtest_type == "standard":
            results = self._run_standard_backtest(data, signals, show_dashboard)
        elif backtest_type == "monte_carlo":
            results = self._run_monte_carlo_backtest(
                data, signals, num_simulations, show_dashboard
            )
        else:
            raise ValueError(f"Unknown backtest_type: {backtest_type}")
        
        # Calculate comprehensive metrics
        if backtest_type == "standard":
            metrics = self.metrics_calc.calculate_all_metrics(
                trades=results['trades'],
                equity_curve=results.get('equity_curve'),
                market_data=data
            )
            results['metrics'] = metrics
            
            # Print results
            runtime = time.time() - start_time
            self._print_results(metrics, runtime, backtest_type)
        else:
            # Monte Carlo results already printed
            runtime = time.time() - start_time
            results['runtime'] = runtime
        
        return results
    
    def _run_standard_backtest(self, 
                               data: pd.DataFrame,
                               signals: pd.DataFrame,
                               show_dashboard: bool) -> Dict:
        """Run standard backtest"""
        simulator = TradeSimulator(initial_balance=self.initial_balance)
        results = simulator.run(signals, data)
        
        # Create dashboard
        if show_dashboard:
            dashboard_path = create_dashboard(data, signals, results['trades'], results['metrics'])
            self.logger.info(f"Dashboard saved to {dashboard_path}")
            # Open dashboard in browser
            open_dashboard_server(dashboard_path, port=8000)
        
        return results
    
    def _run_monte_carlo_backtest(self,
                                 data: pd.DataFrame,
                                 signals: pd.DataFrame,
                                 num_simulations: int,
                                 show_dashboard: bool) -> Dict:
        """Run Monte Carlo backtest"""
        # Calculate parameters from historical data
        returns = data['close'].pct_change().dropna()
        mu = returns.mean() * self.trading_days  # Annualized return
        sigma = returns.std() * np.sqrt(self.trading_days)  # Annualized volatility
        initial_price = data['close'].iloc[-1]
        
        # Initialize Monte Carlo simulator
        mc_simulator = MonteCarloSimulator(
            initial_price=initial_price,
            mu=mu,
            sigma=sigma
        )
        
        # Run simulation
        mc_results = mc_simulator.simulate_trading_paths(
            num_paths=num_simulations,
            num_days=len(data),
            signals=signals,
            initial_balance=self.initial_balance
        )
        
        # Calculate and print summary statistics
        final_values = mc_results['portfolio_paths'][:, -1]
        returns = (final_values - self.initial_balance) / self.initial_balance
        
        # Aggregate metrics across all paths
        all_metrics = mc_results['all_metrics']
        summary_metrics = {
            'num_simulations': num_simulations,
            'avg_final_balance': np.mean(final_values),
            'median_final_balance': np.median(final_values),
            'best_final_balance': np.max(final_values),
            'worst_final_balance': np.min(final_values),
            'avg_return': np.mean(returns),
            'median_return': np.median(returns),
            'std_return': np.std(returns),
            'prob_profit': np.mean(returns > 0),
            'avg_win_rate': np.mean([m['win_rate'] for m in all_metrics]),
            'avg_profit_factor': np.nanmean([m['profit_factor'] for m in all_metrics]),
            'avg_max_drawdown': np.mean([m['max_drawdown'] for m in all_metrics]),
        }
        
        # Calculate Sharpe ratio for Monte Carlo
        if len(returns) > 1 and np.std(returns) > 0:
            summary_metrics['sharpe_ratio'] = np.mean(returns) / np.std(returns) * np.sqrt(self.trading_days)
        else:
            summary_metrics['sharpe_ratio'] = 0.0
        
        # Show dashboard
        if show_dashboard:
            mc_dashboard = MonteCarloDashboard(mc_results, ticker="SIMULATED")
            figures = mc_dashboard.show_dashboard()
            summary_metrics['figures'] = figures
        
        # Print results
        self._print_monte_carlo_results(summary_metrics)
        
        return {
            'mc_results': mc_results,
            'summary_metrics': summary_metrics
        }
    
    def _print_results(self, metrics: Dict, runtime: float, backtest_type: str):
        """Print comprehensive backtest results"""
        print("\n" + MetricsCalculator.format_metrics(metrics))
        print(f"\nRuntime: {runtime:.2f} seconds")
        if backtest_type == "standard":
            print(f"Dashboard saved to: outputs/dashboard.html")
    
    def _print_monte_carlo_results(self, summary_metrics: Dict):
        """Print Monte Carlo simulation results"""
        print("\n" + "=" * 60)
        print("MONTE CARLO SIMULATION RESULTS")
        print("=" * 60)
        print(f"\nNumber of Simulations:    {summary_metrics['num_simulations']:>15}")
        print(f"\n--- Balance Statistics ---")
        print(f"Average Final Balance:    ${summary_metrics['avg_final_balance']:>15,.2f}")
        print(f"Median Final Balance:     ${summary_metrics['median_final_balance']:>15,.2f}")
        print(f"Best Final Balance:       ${summary_metrics['best_final_balance']:>15,.2f}")
        print(f"Worst Final Balance:      ${summary_metrics['worst_final_balance']:>15,.2f}")
        print(f"\n--- Return Statistics ---")
        print(f"Average Return:           {summary_metrics['avg_return']:>15.2%}")
        print(f"Median Return:            {summary_metrics['median_return']:>15.2%}")
        print(f"Std Dev of Returns:       {summary_metrics['std_return']:>15.2%}")
        print(f"Probability of Profit:    {summary_metrics['prob_profit']:>15.2%}")
        if 'sharpe_ratio' in summary_metrics:
            print(f"Sharpe Ratio:             {summary_metrics['sharpe_ratio']:>15.2f}")
        print(f"\n--- Performance Metrics ---")
        print(f"Average Win Rate:         {summary_metrics['avg_win_rate']:>15.2%}")
        print(f"Average Profit Factor:    {summary_metrics['avg_profit_factor']:>15.2f}")
        print(f"Average Max Drawdown:     {summary_metrics['avg_max_drawdown']:>15.2%}")
        print("=" * 60)

