# backtest_rig/core/trade_simulator.py
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dataclasses import dataclass

@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    position_weight: float  # Added to track position weight
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    status: str = "OPEN"  # "OPEN" | "CLOSED"
    reason: Optional[str] = None  # "STOP-LOSS" | "TARGET" | None
    position_type: str = "LONG"  # "LONG" | "SHORT"

class TradeSimulator:
    def __init__(self, initial_balance: float = 10000.0):
        """
        Args:
            initial_balance: Starting capital in USD
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []  # List of current open positions
        self.trade_history = []
        self.commission_rate = 0.001  # 0.1% commission per trade
        
        # Configure logging
        logging.basicConfig(
            filename='outputs/logs/trades.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    def run(self, 
            signals: pd.DataFrame,
            market_data: pd.DataFrame) -> Dict:
        """
        Execute trades based on signals and market data
        
        Args:
            signals: DataFrame with required columns:
                - signal (-1, 0, 1)
                - trade_weight (0.0 to 1.0)
            market_data: DataFrame with required columns:
                - open, high, low, close, volume
            
        Returns:
            Dict containing:
            - trades: List of all executed trades
            - positions: List of current open positions
            - balance: Final account balance
            - metrics: Performance statistics
        """
        # Validate input data
        required_signal_cols = ['signal', 'trade_weight']
        required_market_cols = ['open', 'high', 'low', 'close', 'volume']
        
        if not all(col in signals.columns for col in required_signal_cols):
            raise ValueError(f"Signals DataFrame missing required columns: {required_signal_cols}")
        if not all(col in market_data.columns for col in required_market_cols):
            raise ValueError(f"Market data DataFrame missing required columns: {required_market_cols}")
            
        # Combine market data with signals
        df = market_data.copy()
        df['Signal'] = signals['signal']
        df['trade_weight'] = signals['trade_weight']
        
        for idx, row in df.iterrows():
            current_price = row["close"]
            
            # Update all open positions
            self._update_positions(current_price, idx)
            
            signal = row["Signal"]
            trade_weight = row["trade_weight"]
            
            # Process signals
            if signal != 0 and trade_weight > 0:  # Only process non-zero signals with weight
                if signal == 1:  # Buy signal
                    self._enter_position(
                        entry_price=current_price, 
                        entry_date=idx,
                        position_type="LONG",
                        position_weight=trade_weight
                    )
                elif signal == -1:  # Sell/exit signal
                    # Close positions that have been open longest first
                    positions_to_close = sorted(self.positions, key=lambda x: x.entry_date)
                    for position in positions_to_close:
                        self._exit_position(
                            position=position,
                            exit_price=current_price, 
                            exit_date=idx,
                            reason="SIGNAL"
                        )

        # Close any remaining positions with last price
        final_price = market_data.iloc[-1]['close']
        for position in self.positions[:]:  # Copy list since we're modifying it
            self._exit_position(
                position=position,
                exit_price=final_price,
                exit_date=market_data.index[-1],
                reason="BACKTEST_END"
            )
        
        return {
            'trades': self.trade_history,
            'positions': self.positions,
            'balance': self.balance,
            'metrics': self._calculate_metrics()
        }

    def _enter_position(self, 
                       entry_price: float, 
                       entry_date: pd.Timestamp,
                       position_type: str,
                       position_weight: float,
                       risk_pct: float = 0.02,
                       reward_pct: float = 0.05) -> None:
        """Enter new trade with position sizing"""
        # Calculate position size based on weight (% of balance)
        available_balance = self.balance * position_weight
        shares = available_balance / entry_price
        
        # Calculate commission
        commission = shares * entry_price * self.commission_rate
        
        # Ensure we have enough balance for commission
        if shares * entry_price + commission > available_balance:
            shares = (available_balance / (1 + self.commission_rate)) / entry_price
            commission = shares * entry_price * self.commission_rate
        
        if shares <= 0:
            logging.warning(f"Insufficient balance for trade at {entry_date}")
            return
            
        position = Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            position_weight=position_weight,
            stop_loss=entry_price * (1 - risk_pct),
            target_price=entry_price * (1 + reward_pct),
            position_type=position_type
        )
        
        self.positions.append(position)
        
        # Deduct entry cost including commission
        self.balance -= (shares * entry_price + commission)
        logging.info(
            f"ENTER {position_type}: {shares:.2f} shares at {entry_price:.2f} "
            f"(Weight: {position_weight:.1%}, Commission: ${commission:.2f})"
        )

    def _exit_position(self, 
                      position: Trade,
                      exit_price: float, 
                      exit_date: pd.Timestamp,
                      reason: str) -> None:
        """Close a specific position"""
        if position not in self.positions:
            return
            
        position.exit_date = exit_date
        position.exit_price = exit_price
        position.status = "CLOSED"
        position.reason = reason
        
        # Calculate P/L including commission
        entry_commission = position.shares * position.entry_price * self.commission_rate
        exit_commission = position.shares * exit_price * self.commission_rate
        total_commission = entry_commission + exit_commission
        
        if position.position_type == "LONG":
            pnl = (exit_price - position.entry_price) * position.shares - total_commission
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.shares - total_commission
            
        self.balance += position.shares * exit_price - exit_commission
        
        self.trade_history.append(position)
        self.positions.remove(position)
        
        logging.info(
            f"EXIT {position.position_type}: {position.shares:.2f} shares at {exit_price:.2f} "
            f"| P/L: {pnl:.2f} (Commission: ${total_commission:.2f})"
        )

    def _update_positions(self, current_price: float, current_time: pd.Timestamp) -> None:
        """Update all open positions - check stops and targets"""
        for position in self.positions[:]:  # Copy list since we're modifying it
            if position.position_type == "LONG":
                # Check stop loss
                if current_price <= position.stop_loss:
                    self._exit_position(
                        position=position,
                        exit_price=position.stop_loss,
                        exit_date=current_time,
                        reason="STOP_LOSS"
                    )
                # Check take profit
                elif current_price >= position.target_price:
                    self._exit_position(
                        position=position,
                        exit_price=position.target_price,
                        exit_date=current_time,
                        reason="TARGET"
                    )
            else:  # SHORT position
                # Check stop loss
                if current_price >= position.stop_loss:
                    self._exit_position(
                        position=position,
                        exit_price=position.stop_loss,
                        exit_date=current_time,
                        reason="STOP_LOSS"
                    )
                # Check take profit
                elif current_price <= position.target_price:
                    self._exit_position(
                        position=position,
                        exit_price=position.target_price,
                        exit_date=current_time,
                        reason="TARGET"
                    )

    def _calculate_metrics(self) -> Dict:
        """Generate performance statistics"""
        closed_trades = [t for t in self.trade_history if t.status == "CLOSED"]
        
        if not closed_trades:
            return {
                'initial_balance': self.initial_balance,
                'final_balance': self.balance,
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0
            }
            
        # Calculate metrics
        total_trades = len(closed_trades)
        win_rate = self._calculate_win_rate(closed_trades)
        profit_factor = self._calculate_profit_factor(closed_trades)
        max_drawdown = self._calculate_max_drawdown(closed_trades)
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown
        }

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """Calculate maximum drawdown from trade history"""
        equity = self.initial_balance
        peak = equity
        max_drawdown = 0.0
        
        for trade in trades:
            pnl = self._calculate_trade_pnl(trade)
            equity += pnl
            
            if equity > peak:
                peak = equity
            else:
                drawdown = (peak - equity) / peak
                max_drawdown = max(max_drawdown, drawdown)
                
        return max_drawdown

    def _calculate_trade_pnl(self, trade: Trade) -> float:
        """Calculate P/L for a single trade including commission"""
        entry_commission = trade.shares * trade.entry_price * self.commission_rate
        exit_commission = trade.shares * trade.exit_price * self.commission_rate
        total_commission = entry_commission + exit_commission
        
        if trade.position_type == "LONG":
            return (trade.exit_price - trade.entry_price) * trade.shares - total_commission
        else:  # SHORT
            return (trade.entry_price - trade.exit_price) * trade.shares - total_commission

    @staticmethod
    def _calculate_win_rate(trades: List[Trade]) -> float:
        if not trades:
            return 0.0
            
        winning_trades = []
        for trade in trades:
            # Calculate P/L including commission
            entry_commission = trade.shares * trade.entry_price * 0.001
            exit_commission = trade.shares * trade.exit_price * 0.001
            total_commission = entry_commission + exit_commission
            
            if trade.position_type == "LONG":
                pnl = (trade.exit_price - trade.entry_price) * trade.shares - total_commission
            else:  # SHORT
                pnl = (trade.entry_price - trade.exit_price) * trade.shares - total_commission
                
            if pnl > 0:
                winning_trades.append(trade)
                
        return len(winning_trades) / len(trades)

    @staticmethod
    def _calculate_profit_factor(trades: List[Trade]) -> float:
        gains = losses = 0.0
        for trade in trades:
            # Calculate P/L including commission
            entry_commission = trade.shares * trade.entry_price * 0.001
            exit_commission = trade.shares * trade.exit_price * 0.001
            total_commission = entry_commission + exit_commission
            
            if trade.position_type == "LONG":
                pnl = (trade.exit_price - trade.entry_price) * trade.shares - total_commission
            else:  # SHORT
                pnl = (trade.entry_price - trade.exit_price) * trade.shares - total_commission
                
            if pnl > 0:
                gains += pnl
            else:
                losses += abs(pnl)
        return gains / losses if losses > 0 else float('inf')