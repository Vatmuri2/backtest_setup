# core/metrics.py
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from .trade_simulator import Trade

class MetricsCalculator:
    """Comprehensive performance metrics calculator"""
    
    def __init__(self, initial_balance: float, trading_days: int = 252):
        """
        Args:
            initial_balance: Starting capital
            trading_days: Number of trading days per year (default 252)
        """
        self.initial_balance = initial_balance
        self.trading_days = trading_days
    
    def calculate_all_metrics(self, 
                              trades: List[Trade],
                              equity_curve: Optional[pd.Series] = None,
                              market_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades: List of completed trades
            equity_curve: Series of portfolio values over time
            market_data: Market data DataFrame (for benchmark comparison)
        
        Returns:
            Dictionary of all calculated metrics
        """
        closed_trades = [t for t in trades if t.status == "CLOSED"]
        
        # Basic metrics
        metrics = {
            'initial_balance': self.initial_balance,
            'final_balance': self._get_final_balance(trades, equity_curve),
            'total_trades': len(closed_trades),
            'win_rate': self._calculate_win_rate(closed_trades),
            'profit_factor': self._calculate_profit_factor(closed_trades),
            'max_drawdown': self._calculate_max_drawdown(trades, equity_curve),
        }
        
        # Return metrics
        total_return = (metrics['final_balance'] - self.initial_balance) / self.initial_balance
        metrics['total_return'] = total_return
        
        # Annualized return (if we have time period info)
        if equity_curve is not None and len(equity_curve) > 1:
            days = len(equity_curve)
            years = days / self.trading_days
            if years > 0:
                metrics['annualized_return'] = (1 + total_return) ** (1 / years) - 1
            else:
                metrics['annualized_return'] = 0.0
        else:
            metrics['annualized_return'] = None
        
        # Risk metrics
        if equity_curve is not None and len(equity_curve) > 1:
            returns = equity_curve.pct_change().dropna()
            if len(returns) > 0:
                metrics['volatility'] = returns.std() * np.sqrt(self.trading_days)
                metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(returns)
                metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns)
                metrics['calmar_ratio'] = self._calculate_calmar_ratio(
                    metrics['annualized_return'], 
                    metrics['max_drawdown']
                )
            else:
                metrics['volatility'] = 0.0
                metrics['sharpe_ratio'] = 0.0
                metrics['sortino_ratio'] = 0.0
                metrics['calmar_ratio'] = 0.0
        else:
            metrics['volatility'] = None
            metrics['sharpe_ratio'] = None
            metrics['sortino_ratio'] = None
            metrics['calmar_ratio'] = None
        
        # Trade statistics
        if closed_trades:
            trade_returns = [self._calculate_trade_return(t) for t in closed_trades]
            metrics['avg_trade_return'] = np.mean(trade_returns)
            metrics['best_trade'] = max(trade_returns) if trade_returns else 0.0
            metrics['worst_trade'] = min(trade_returns) if trade_returns else 0.0
            metrics['avg_win'] = np.mean([r for r in trade_returns if r > 0]) if any(r > 0 for r in trade_returns) else 0.0
            metrics['avg_loss'] = np.mean([r for r in trade_returns if r < 0]) if any(r < 0 for r in trade_returns) else 0.0
        else:
            metrics['avg_trade_return'] = 0.0
            metrics['best_trade'] = 0.0
            metrics['worst_trade'] = 0.0
            metrics['avg_win'] = 0.0
            metrics['avg_loss'] = 0.0
        
        # Win/loss statistics
        if closed_trades:
            winning_trades = [t for t in closed_trades if self._calculate_trade_pnl(t) > 0]
            losing_trades = [t for t in closed_trades if self._calculate_trade_pnl(t) < 0]
            metrics['total_wins'] = len(winning_trades)
            metrics['total_losses'] = len(losing_trades)
            metrics['largest_win'] = max([self._calculate_trade_pnl(t) for t in winning_trades]) if winning_trades else 0.0
            metrics['largest_loss'] = min([self._calculate_trade_pnl(t) for t in losing_trades]) if losing_trades else 0.0
        else:
            metrics['total_wins'] = 0
            metrics['total_losses'] = 0
            metrics['largest_win'] = 0.0
            metrics['largest_loss'] = 0.0
        
        return metrics
    
    def _get_final_balance(self, trades: List[Trade], equity_curve: Optional[pd.Series]) -> float:
        """Get final balance from equity curve or calculate from trades"""
        if equity_curve is not None and len(equity_curve) > 0:
            return equity_curve.iloc[-1]
        
        # Calculate from trades
        balance = self.initial_balance
        for trade in trades:
            if trade.status == "CLOSED":
                balance += self._calculate_trade_pnl(trade)
        return balance
    
    def _calculate_trade_pnl(self, trade: Trade) -> float:
        """Calculate P/L for a single trade including commission"""
        commission_rate = 0.001
        entry_commission = trade.shares * trade.entry_price * commission_rate
        exit_commission = trade.shares * trade.exit_price * commission_rate
        total_commission = entry_commission + exit_commission
        
        if trade.position_type == "LONG":
            return (trade.exit_price - trade.entry_price) * trade.shares - total_commission
        else:  # SHORT
            return (trade.entry_price - trade.exit_price) * trade.shares - total_commission
    
    def _calculate_trade_return(self, trade: Trade) -> float:
        """Calculate return percentage for a single trade"""
        pnl = self._calculate_trade_pnl(trade)
        cost = trade.shares * trade.entry_price
        return pnl / cost if cost > 0 else 0.0
    
    def _calculate_win_rate(self, trades: List[Trade]) -> float:
        """Calculate win rate"""
        if not trades:
            return 0.0
        winning = sum(1 for t in trades if self._calculate_trade_pnl(t) > 0)
        return winning / len(trades)
    
    def _calculate_profit_factor(self, trades: List[Trade]) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        gains = losses = 0.0
        for trade in trades:
            pnl = self._calculate_trade_pnl(trade)
            if pnl > 0:
                gains += pnl
            else:
                losses += abs(pnl)
        return gains / losses if losses > 0 else float('inf')
    
    def _calculate_max_drawdown(self, trades: List[Trade], equity_curve: Optional[pd.Series]) -> float:
        """Calculate maximum drawdown"""
        if equity_curve is not None and len(equity_curve) > 0:
            peak = equity_curve.expanding().max()
            drawdown = (equity_curve - peak) / peak
            return abs(drawdown.min())
        
        # Calculate from trades if no equity curve
        equity = self.initial_balance
        peak = equity
        max_drawdown = 0.0
        
        for trade in trades:
            if trade.status == "CLOSED":
                equity += self._calculate_trade_pnl(trade)
                if equity > peak:
                    peak = equity
                else:
                    drawdown = (peak - equity) / peak
                    max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / self.trading_days)
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(self.trading_days)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / self.trading_days)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0
        
        sortino = excess_returns.mean() / downside_returns.std() * np.sqrt(self.trading_days)
        return sortino
    
    def _calculate_calmar_ratio(self, annualized_return: Optional[float], max_drawdown: float) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown)"""
        if annualized_return is None or max_drawdown == 0:
            return 0.0
        return annualized_return / max_drawdown if max_drawdown > 0 else 0.0
    
    @staticmethod
    def format_metrics(metrics: Dict) -> str:
        """Format metrics for printing"""
        lines = []
        lines.append("=" * 60)
        lines.append("BACKTEST PERFORMANCE METRICS")
        lines.append("=" * 60)
        
        # Balance metrics
        lines.append("\n--- Balance ---")
        lines.append(f"Initial Balance:      ${metrics['initial_balance']:>15,.2f}")
        lines.append(f"Final Balance:        ${metrics['final_balance']:>15,.2f}")
        lines.append(f"Total Return:         {metrics['total_return']:>15.2%}")
        if metrics['annualized_return'] is not None:
            lines.append(f"Annualized Return:    {metrics['annualized_return']:>15.2%}")
        
        # Risk metrics
        lines.append("\n--- Risk Metrics ---")
        lines.append(f"Max Drawdown:         {metrics['max_drawdown']:>15.2%}")
        if metrics['volatility'] is not None:
            lines.append(f"Volatility (Annual):  {metrics['volatility']:>15.2%}")
        if metrics['sharpe_ratio'] is not None:
            lines.append(f"Sharpe Ratio:         {metrics['sharpe_ratio']:>15.2f}")
        if metrics['sortino_ratio'] is not None:
            lines.append(f"Sortino Ratio:        {metrics['sortino_ratio']:>15.2f}")
        if metrics['calmar_ratio'] is not None:
            lines.append(f"Calmar Ratio:         {metrics['calmar_ratio']:>15.2f}")
        
        # Trade statistics
        lines.append("\n--- Trade Statistics ---")
        lines.append(f"Total Trades:         {metrics['total_trades']:>15}")
        lines.append(f"Winning Trades:       {metrics['total_wins']:>15}")
        lines.append(f"Losing Trades:        {metrics['total_losses']:>15}")
        lines.append(f"Win Rate:             {metrics['win_rate']:>15.2%}")
        lines.append(f"Profit Factor:        {metrics['profit_factor']:>15.2f}")
        
        # Trade returns
        lines.append("\n--- Trade Returns ---")
        lines.append(f"Avg Trade Return:     {metrics['avg_trade_return']:>15.2%}")
        lines.append(f"Best Trade:           {metrics['best_trade']:>15.2%}")
        lines.append(f"Worst Trade:          {metrics['worst_trade']:>15.2%}")
        lines.append(f"Avg Win:              {metrics['avg_win']:>15.2%}")
        lines.append(f"Avg Loss:             {metrics['avg_loss']:>15.2%}")
        lines.append(f"Largest Win:          ${metrics['largest_win']:>15,.2f}")
        lines.append(f"Largest Loss:         ${metrics['largest_loss']:>15,.2f}")
        
        lines.append("=" * 60)
        return "\n".join(lines)

