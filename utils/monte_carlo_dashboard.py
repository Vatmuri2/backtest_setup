import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from core.monte_carlo import MonteCarloSimulator

class MonteCarloDashboard:
    """
    Visualizes results from Monte Carlo trading simulations
    """
    def __init__(self, simulation_results: Dict, ticker: str = "AAPL"):
        """
        Initialize dashboard with simulation results
        
        Parameters:
        - simulation_results: Output from MonteCarloSimulator.simulate_trading_paths()
        """
        self.results = simulation_results
        self.ticker = ticker
    
    # In your dashboard code:
    def plot_price_paths(self) -> plt.Figure:
        """Plot all simulated price paths"""
        price_paths = self.results['price_paths'][:, :, 3]  # Close prices
        initial_price = price_paths[0, 0] if price_paths.size > 0 else 0
        
        fig, ax = plt.subplots(figsize=(12, 6))
        for i in range(price_paths.shape[0]):
            ax.plot(price_paths[i], alpha=0.4, lw=1)
        
        if initial_price > 0:
            ax.axhline(initial_price, color='k', linestyle='--', 
                    label=f'Initial Price (${initial_price:.2f})')
        
        ax.set_title(f'Simulated Price Paths ({self.ticker})' if hasattr(self, 'ticker') else 'Simulated Price Paths')
        ax.set_xlabel('Trading Days')
        ax.set_ylabel('Price ($)')
        if initial_price > 0:
            ax.legend()
        ax.grid(True)
        return fig
    
    def plot_portfolio_paths(self) -> plt.Figure:
        """
        Plot all portfolio value paths
        
        Returns:
        - Matplotlib Figure object
        """
        portfolio_paths = self.results['portfolio_paths']
        num_paths, num_days = portfolio_paths.shape
        
        fig, ax = plt.subplots(figsize=(12, 6))
        for i in range(num_paths):
            ax.plot(portfolio_paths[i], alpha=0.4, lw=1)
        
        # Add median path
        median_path = np.median(portfolio_paths, axis=0)
        ax.plot(median_path, 'k-', lw=3, label='Median')
        
        ax.set_title(f'Portfolio Value Paths ({num_paths} scenarios)')
        ax.set_xlabel('Trading Days')
        ax.set_ylabel('Portfolio Value ($)')
        ax.legend()
        ax.grid(True)
        
        return fig
    
    def plot_performance_distribution(self) -> plt.Figure:
        """
        Plot distribution of final portfolio values
        
        Returns:
        - Matplotlib Figure object
        """
        final_values = self.results['portfolio_paths'][:, -1]
        metrics = self.results['all_metrics']
        
        # Calculate additional metrics
        initial_balance = metrics[0]['initial_balance']
        returns = (final_values - initial_balance) / initial_balance
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Portfolio value distribution
        sns.histplot(final_values, kde=True, ax=ax1)
        ax1.axvline(np.median(final_values), color='r', linestyle='--', label='Median')
        ax1.axvline(initial_balance, color='g', linestyle='--', label='Initial')
        ax1.set_title('Distribution of Final Portfolio Values')
        ax1.set_xlabel('Final Portfolio Value ($)')
        ax1.legend()
        
        # Returns distribution
        sns.histplot(returns, kde=True, ax=ax2)
        ax2.axvline(np.median(returns), color='r', linestyle='--', label='Median')
        ax2.axvline(0, color='g', linestyle='--', label='Break-even')
        ax2.set_title('Distribution of Returns')
        ax2.set_xlabel('Return (%)')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        ax2.legend()
        
        return fig
    
    def plot_metrics_summary(self) -> plt.Figure:
        """
        Plot summary statistics of performance metrics
        
        Returns:
        - Matplotlib Figure object
        """
        metrics = pd.DataFrame(self.results['all_metrics'])
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Win Rate
        sns.boxplot(y=metrics['win_rate'], ax=axes[0, 0])
        axes[0, 0].set_title('Win Rate Distribution')
        axes[0, 0].set_ylabel('Win Rate')
        axes[0, 0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        
        # Profit Factor
        profit_factor = metrics['profit_factor'].replace([np.inf], np.nan)
        sns.boxplot(y=profit_factor, ax=axes[0, 1])
        axes[0, 1].set_title('Profit Factor Distribution')
        axes[0, 1].set_ylabel('Profit Factor')
        
        # Max Drawdown
        sns.boxplot(y=metrics['max_drawdown'], ax=axes[1, 0])
        axes[1, 0].set_title('Max Drawdown Distribution')
        axes[1, 0].set_ylabel('Max Drawdown')
        axes[1, 0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        
        # Final Balance
        sns.boxplot(y=metrics['final_balance'], ax=axes[1, 1])
        axes[1, 1].set_title('Final Balance Distribution')
        axes[1, 1].set_ylabel('Final Balance ($)')
        
        return fig
    
    def plot_extreme_cases(self) -> plt.Figure:
        """
        Plot best, worst, and median scenarios
        
        Returns:
        - Matplotlib Figure object
        """
        portfolio_paths = self.results['portfolio_paths']
        price_paths = self.results['price_paths'][:, :, 3]  # Close prices
        final_values = portfolio_paths[:, -1]
        
        best_idx = np.argmax(final_values)
        worst_idx = np.argmin(final_values)
        median_idx = np.argsort(final_values)[len(final_values) // 2]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Price paths
        ax1.plot(price_paths[best_idx], label=f'Best Case (Final: ${final_values[best_idx]:,.2f})')
        ax1.plot(price_paths[worst_idx], label=f'Worst Case (Final: ${final_values[worst_idx]:,.2f})')
        ax1.plot(price_paths[median_idx], label=f'Median Case (Final: ${final_values[median_idx]:,.2f})')
        ax1.set_title('Price Paths: Best/Worst/Median Cases')
        ax1.set_xlabel('Trading Days')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True)
        
        # Portfolio paths
        ax2.plot(portfolio_paths[best_idx], label='Best Case')
        ax2.plot(portfolio_paths[worst_idx], label='Worst Case')
        ax2.plot(portfolio_paths[median_idx], label='Median Case')
        ax2.set_title('Portfolio Value: Best/Worst/Median Cases')
        ax2.set_xlabel('Trading Days')
        ax2.set_ylabel('Portfolio Value ($)')
        ax2.legend()
        ax2.grid(True)
        
        return fig
    
    def show_dashboard(self):
        """
        Display complete dashboard with all visualizations
        """
        plt.close('all')
        
        # Create figures
        fig1 = self.plot_price_paths()
        fig2 = self.plot_portfolio_paths()
        fig3 = self.plot_performance_distribution()
        fig4 = self.plot_metrics_summary()
        fig5 = self.plot_extreme_cases()
        
        # Show all figures
        plt.show()
        
        return {
            'price_paths': fig1,
            'portfolio_paths': fig2,
            'performance_distribution': fig3,
            'metrics_summary': fig4,
            'extreme_cases': fig5
        }