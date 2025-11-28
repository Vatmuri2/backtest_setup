# Creating Your Own Strategy

This guide shows you how to create and test your own trading strategies.

## Quick Start

1. **Copy the template:**
   ```bash
   cp strategies/strategy_template.py strategies/my_strategy.py
   ```

2. **Edit the strategy file:**
   - Rename `TemplateStrategy` to your strategy name
   - Implement your trading logic in `generate_signals()`
   - Adjust parameters in `__init__()`

3. **Use in main.py:**
   ```python
   from strategies.my_strategy import MyStrategy
   
   strategy = MyStrategy(param1=1.0, param2=2.0)
   ```

## Strategy Requirements

Your strategy class must:
- Inherit from `BaseStrategy`
- Implement `generate_signals(data: pd.DataFrame) -> pd.DataFrame`

## Signal Format

The `generate_signals()` method must return a DataFrame with:
- **index**: Same as input data (dates)
- **'signal'**: 
  - `1` = BUY
  - `0` = HOLD
  - `-1` = SELL
- **'trade_weight'**: Position size as fraction of capital (0.0 to 1.0)

## Example: Simple Moving Average Crossover

```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0
    signals['trade_weight'] = 0.0
    
    sma_short = data['close'].rolling(window=10).mean()
    sma_long = data['close'].rolling(window=30).mean()
    
    for i in range(1, len(data)):
        # Buy when short MA crosses above long MA
        if sma_short.iloc[i] > sma_long.iloc[i] and sma_short.iloc[i-1] <= sma_long.iloc[i-1]:
            signals.iloc[i, signals.columns.get_loc('signal')] = 1
            signals.iloc[i, signals.columns.get_loc('trade_weight')] = 0.2
        
        # Sell when short MA crosses below long MA
        elif sma_short.iloc[i] < sma_long.iloc[i] and sma_short.iloc[i-1] >= sma_long.iloc[i-1]:
            signals.iloc[i, signals.columns.get_loc('signal')] = -1
            signals.iloc[i, signals.columns.get_loc('trade_weight')] = 0.2
    
    return signals
```

## Available Data

The `data` DataFrame contains:
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume
- `index`: Datetime index

## Testing Your Strategy

1. Create your strategy file
2. Import it in `main.py`
3. Run: `python main.py`
4. View results in the automatically opened dashboard

## Tips

- Start simple and test frequently
- Use `calculate_indicators()` for complex indicator calculations
- Test with different parameters
- Try both "standard" and "monte_carlo" backtest types
- Check the metrics output for strategy performance

