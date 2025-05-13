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
        self.current_position: Optional[Trade] = None
        self.trade_history: List[Trade] = []
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
            signals: DataFrame with 'signal' column (-1, 0, 1)
            market_data: Raw OHLC data with 'close' price
            
        Returns:
            Dict containing:
            - trades: List of all executed trades
            - current_position: Open trade (if any)
            - balance: Final account balance
            - metrics: Performance statistics
        """
        for idx, row in signals.iterrows():
            price = market_data.loc[idx, 'close']
            self._process_signal(row['signal'], price, idx)
        
        self._update_open_position(market_data.iloc[-1]['close'])
        
        return {
            'trades': self.trade_history,
            'current_position': self.current_position,
            'balance': self.balance,
            'metrics': self._calculate_metrics()
        }

    def _process_signal(self, 
                       signal: int, 
                       price: float, 
                       timestamp: pd.Timestamp) -> None:
        """Handle buy/sell signals"""
        if signal == 1 and not self.current_position:
            self._enter_position(price, timestamp, "LONG")
        elif signal == -1 and not self.current_position:
            self._enter_position(price, timestamp, "SHORT")
        elif signal == -1 and self.current_position and self.current_position.position_type == "LONG":
            self._exit_position(price, timestamp, reason="SIGNAL")
        elif signal == 1 and self.current_position and self.current_position.position_type == "SHORT":
            self._exit_position(price, timestamp, reason="SIGNAL")

    def _enter_position(self, 
                       entry_price: float, 
                       entry_date: pd.Timestamp,
                       position_type: str,
                       risk_pct: float = 0.02,
                       reward_pct: float = 0.05) -> None:
        """Enter new trade with position sizing"""
        # Calculate position size (95% of balance to account for commission)
        available_balance = self.balance * 0.95
        shares = available_balance / entry_price
        
        # Calculate commission
        commission = shares * entry_price * self.commission_rate
        
        self.current_position = Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            stop_loss=entry_price * (1 - risk_pct),
            target_price=entry_price * (1 + reward_pct),
            position_type=position_type
        )
        
        # Deduct entry cost including commission
        self.balance -= (shares * entry_price + commission)
        logging.info(f"ENTER {position_type}: {shares:.2f} shares at {entry_price:.2f} (Commission: ${commission:.2f})")

    def _exit_position(self, 
                      exit_price: float, 
                      exit_date: pd.Timestamp,
                      reason: str) -> None:
        """Close current position"""
        if not self.current_position:
            return
            
        trade = self.current_position
        trade.exit_date = exit_date
        trade.exit_price = exit_price
        trade.status = "CLOSED"
        trade.reason = reason
        
        # Calculate P/L including commission
        entry_commission = trade.shares * trade.entry_price * self.commission_rate
        exit_commission = trade.shares * exit_price * self.commission_rate
        total_commission = entry_commission + exit_commission
        
        if trade.position_type == "LONG":
            pnl = (exit_price - trade.entry_price) * trade.shares - total_commission
        else:  # SHORT
            pnl = (trade.entry_price - exit_price) * trade.shares - total_commission
            
        self.balance += trade.shares * exit_price - exit_commission
        
        self.trade_history.append(trade)
        self.current_position = None
        
        logging.info(
            f"EXIT {trade.position_type}: {trade.shares:.2f} shares at {exit_price:.2f} "
            f"| P/L: {pnl:.2f} (Commission: ${total_commission:.2f})"
        )

    def _update_open_position(self, latest_price: float) -> None:
        """Update unrealized P/L for open positions"""
        if self.current_position:
            # Check stop-loss/target
            if self.current_position.position_type == "LONG":
                if latest_price <= self.current_position.stop_loss:
                    self._exit_position(
                        self.current_position.stop_loss,
                        pd.Timestamp.now(),
                        "STOP-LOSS"
                    )
                elif latest_price >= self.current_position.target_price:
                    self._exit_position(
                        self.current_position.target_price,
                        pd.Timestamp.now(),
                        "TARGET"
                    )
            else:  # SHORT
                if latest_price >= self.current_position.stop_loss:
                    self._exit_position(
                        self.current_position.stop_loss,
                        pd.Timestamp.now(),
                        "STOP-LOSS"
                    )
                elif latest_price <= self.current_position.target_price:
                    self._exit_position(
                        self.current_position.target_price,
                        pd.Timestamp.now(),
                        "TARGET"
                    )

    def _calculate_metrics(self) -> Dict:
        """Generate performance statistics"""
        closed_trades = [t for t in self.trade_history if t.status == "CLOSED"]
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_trades': len(closed_trades),
            'win_rate': self._calculate_win_rate(closed_trades),
            'profit_factor': self._calculate_profit_factor(closed_trades)
        }

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