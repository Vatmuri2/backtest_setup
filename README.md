# Backtesting Rig

A streamlined backtesting framework for trading strategies.

## Quick Start

```python
from core.backtest_engine import BacktestEngine
from strategies.mean_reversion_strategy import MeanReversionStrategy, StrategyConfig

# Initialize engine
engine = BacktestEngine(
    api_key="your_api_key",  # or set POLYGON_API_KEY env var
    initial_balance=10000.0
)

# Create strategy
strategy = MeanReversionStrategy(
    threshold_pct=0.5,
    max_position_weight=0.3,
    sensitivity=2.0,
    max_positions=5
)

# Run backtest - dashboard opens automatically in browser!
results = engine.run(
    strategy=strategy,
    symbol="PLTR",
    start_date="2023-01-01",
    backtest_type="standard",  # or "monte_carlo"
    show_dashboard=True  # Opens on http://localhost:8000
)
```

## Creating Your Own Strategy

1. **Copy the template:**
   ```bash
   cp strategies/strategy_template.py strategies/my_strategy.py
   ```

2. **Edit the strategy** - implement your trading logic in `generate_signals()`

3. **Use in main.py:**
   ```python
   from strategies.my_strategy import MyStrategy
   strategy = MyStrategy(param1=1.0, param2=2.0)
   ```

See `strategies/README.md` for detailed instructions.

## Features

- **Simple Interface**: One function call with strategy and backtest type
- **Comprehensive Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio, annualized returns, and more
- **Multiple Backtest Types**: Standard backtest or Monte Carlo simulation
- **Automatic Reporting**: All metrics printed automatically
- **Interactive Dashboards**: Plotly dashboards automatically open in browser (port 8000)
- **Easy Strategy Creation**: Template file and guide for creating custom strategies

## Project Structure

```
backtest_setup/
├── core/
│   ├── backtest_engine.py    # Main backtesting engine
│   ├── metrics.py            # Comprehensive metrics calculator
│   ├── trade_simulator.py    # Trade execution simulator
│   ├── data_fetcher.py       # Market data fetcher
│   └── monte_carlo.py        # Monte Carlo simulator
├── strategies/
│   ├── base_strategy.py      # Base strategy interface
│   └── mean_reversion_strategy.py  # Example strategy
├── utils/
│   ├── dashboard.py          # Standard backtest dashboard
│   ├── monte_carlo_dashboard.py  # Monte Carlo dashboard
│   └── logger.py             # Logging utilities
└── main.py                   # Simple example usage
```

## Metrics Included

- **Returns**: Total return, annualized return
- **Risk Metrics**: Volatility, max drawdown, Sharpe ratio, Sortino ratio, Calmar ratio
- **Trade Statistics**: Win rate, profit factor, average trade return
- **Trade Analysis**: Best/worst trades, average win/loss, largest win/loss

## Backtest Types

### Standard Backtest
Runs strategy on historical data with full metrics and interactive dashboard.

### Monte Carlo Simulation
Runs multiple simulated price paths to evaluate strategy robustness with statistical analysis.
