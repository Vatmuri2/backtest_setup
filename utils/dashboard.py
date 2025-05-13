import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict
from core.trade_simulator import Trade

def create_dashboard(data: pd.DataFrame, 
                    signals: pd.DataFrame,
                    trades: List[Trade],
                    metrics: Dict) -> None:
    """Create interactive dashboard with price, RSI, and trade visualization"""
    
    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, 
                       shared_xaxes=True,
                       vertical_spacing=0.05,
                       row_heights=[0.7, 0.3])

    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price'
        ),
        row=1, col=1
    )

    # Add RSI
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=signals['rsi'],
            name='RSI',
            line=dict(color='purple')
        ),
        row=2, col=1
    )

    # Add overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Add buy/sell markers
    buy_signals = signals[signals['signal'] == 1]
    sell_signals = signals[signals['signal'] == -1]

    fig.add_trace(
        go.Scatter(
            x=buy_signals.index,
            y=data.loc[buy_signals.index, 'low'] * 0.99,  # Slightly below price
            mode='markers',
            name='Buy',
            marker=dict(
                symbol='triangle-up',
                size=15,
                color='green'
            )
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=sell_signals.index,
            y=data.loc[sell_signals.index, 'high'] * 1.01,  # Slightly above price
            mode='markers',
            name='Sell',
            marker=dict(
                symbol='triangle-down',
                size=15,
                color='red'
            )
        ),
        row=1, col=1
    )

    # Add trade annotations
    for trade in trades:
        if trade.status == "CLOSED":
            # Calculate profit/loss
            pnl = (trade.exit_price - trade.entry_price) * trade.shares
            color = 'green' if pnl > 0 else 'red'
            
            # Add entry annotation
            fig.add_annotation(
                x=trade.entry_date,
                y=trade.entry_price,
                text=f"Entry<br>${trade.entry_price:.2f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40,
                row=1, col=1
            )
            
            # Add exit annotation
            fig.add_annotation(
                x=trade.exit_date,
                y=trade.exit_price,
                text=f"Exit<br>${trade.exit_price:.2f}<br>P/L: ${pnl:.2f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=40,
                row=1, col=1
            )

    # Update layout
    fig.update_layout(
        title='RSI Strategy Backtest Results',
        xaxis_title='Date',
        yaxis_title='Price',
        height=1000,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )

    # Add metrics as annotations
    metrics_text = (
        f"Initial Balance: ${metrics['initial_balance']:,.2f}<br>"
        f"Final Balance: ${metrics['final_balance']:,.2f}<br>"
        f"Win Rate: {metrics['win_rate']:.1%}<br>"
        f"Total Trades: {metrics['total_trades']}"
    )
    
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref='paper',
        yref='paper',
        text=metrics_text,
        showarrow=False,
        bgcolor='white',
        bordercolor='black',
        borderwidth=1,
        borderpad=4
    )

    # Save to HTML file
    fig.write_html('outputs/dashboard.html')

def calculate_equity_curve(trades: List[Trade], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """Calculate equity curve from trades"""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    equity = pd.Series(10000, index=dates)  # Start with initial balance
    
    for trade in trades:
        if trade.status == "CLOSED":
            pnl = (trade.exit_price - trade.entry_price) * trade.shares
            equity[trade.exit_date:] += pnl
    
    return pd.DataFrame({'equity': equity}) 