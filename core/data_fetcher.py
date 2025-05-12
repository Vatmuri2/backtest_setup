# backtest_rig/core/data_fetcher.py
import os
import time
from datetime import datetime
from typing import Optional
import pandas as pd
from polygon.rest import RESTClient
from tenacity import retry, stop_after_attempt, wait_exponential

class DataFetcher:
    """Enhanced Polygon.io data fetcher with robust error handling and rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Polygon API key. Defaults to POLYGON_API_KEY environment variable.
        """
        self.client = RESTClient(api_key or os.getenv("POLYGON_API_KEY"))
        self._last_request_time = None
        self._min_request_interval = 0.2  # 5 requests/second (Polygon free tier)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _throttled_request(self):
        """Ensures compliant rate limiting"""
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def get_historical_data(self, symbol: str, start_date: str, 
                          end_date: Optional[str] = None,
                          timespan: str = "day") -> pd.DataFrame:
        """
        Fetches OHLCV data with automatic date handling and retries.
        
        Args:
            symbol: Ticker symbol (e.g. "AAPL")
            start_date: Start date in YYYY-MM-DD format
            end_date: Optional end date (defaults to today)
            timespan: "minute", "hour", "day", etc.
            
        Returns:
            pd.DataFrame with columns: open, high, low, close, volume
        """
        end_date = end_date or datetime.today().strftime("%Y-%m-%d")
        bars = []
        
        try:
            for bar in self.client.list_aggs(
                symbol, 1, timespan, start_date, end_date, limit=50000
            ):
                self._throttled_request()
                bars.append({
                    "date": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume
                })
                
            df = pd.DataFrame(bars)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], unit='ms')
                df.set_index("date", inplace=True)
            return df
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {symbol}: {str(e)}")

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Fetches last traded price with error handling"""
        try:
            self._throttled_request()
            last_trade = self.client.get_last_trade(symbol)
            return last_trade.price if last_trade else None
        except Exception as e:
            print(f"Warning: Failed to get price for {symbol}: {str(e)}")
            return None