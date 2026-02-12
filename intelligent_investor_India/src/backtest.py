import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class Backtester:
    def __init__(self, buy_list_path, years=3):
        self.buy_list_path = buy_list_path
        self.years = years
        self.tickers = self.load_tickers()

    def load_tickers(self):
        try:
            df = pd.read_csv(self.buy_list_path)
            # Standardize column names (Handle 'ticker' vs 'Ticker')
            if 'ticker' in df.columns:
                return df['ticker'].tolist()
            elif 'Ticker' in df.columns:
                return df['Ticker'].tolist()
            else:
                print("❌ Error: Buy List CSV must have a 'ticker' column.")
                return []
        except FileNotFoundError:
            print("❌ Error: Buy List file not found. Run main.py first.")
            return []

    def run_backtest(self):
        if not self.tickers:
            print("⚠ No tickers to backtest.")
            return

        print(f"\n--- ⏳ BACKTESTING ({self.years} Years) ---")
        print(f"Testing Strategy on: {', '.join(self.tickers[:5])}...")

        start_date = (datetime.now() - timedelta(days=self.years*365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        # Download historical data for all tickers + NIFTY 50 (Benchmark)
        tickers_with_benchmark = self.tickers + ['^NSEI']
        
        try:
            # Download ALL data first without selecting a column
            data_raw = yf.download(tickers_with_benchmark, start=start_date, end=end_date, progress=True)
        except Exception as e:
            print(f"❌ Data download critical error: {e}")
            return

        if data_raw.empty:
            print("❌ No data fetched for backtest. Check internet connection.")
            return

        # --- SAFETY CHECK: Find the Price Column ---
        # Newer yfinance versions might return 'Close' instead of 'Adj Close'
        target_col = None
        
        # Check if MultiIndex columns exist (common in new yfinance)
        if isinstance(data_raw.columns, pd.MultiIndex):
            # Check levels for 'Adj Close' or 'Close'
            if 'Adj Close' in data_raw.columns.get_level_values(0):
                target_col = 'Adj Close'
            elif 'Close' in data_raw.columns.get_level_values(0):
                print("⚠ Note: 'Adj Close' missing. Using 'Close' for calculations.")
                target_col = 'Close'
        else:
            # Flat columns
            if 'Adj Close' in data_raw.columns:
                target_col = 'Adj Close'
            elif 'Close' in data_raw.columns:
                print("⚠ Note: 'Adj Close' missing. Using 'Close' for calculations.")
                target_col = 'Close'

        if not target_col:
            print(f"❌ Error: Neither 'Adj Close' nor 'Close' found in data.")
            return

        # Extract the price data
        data = data_raw[target_col]

        # Handle Missing Data (Drop columns that failed to download completely)
        data = data.dropna(axis=1, how='all')
        
        # --- FIX FOR PANDAS 3.0+ ---
        # Use ffill() and bfill() instead of fillna(method='...')
        data = data.ffill().bfill()

        # Normalize to 100 (Start at 100 to compare performance)
        try:
            normalized_data = (data / data.iloc[0]) * 100
        except Exception as e:
            print(f"❌ Error during normalization: {e}")
            return
        
        # Calculate Strategy Portfolio (Equal Weight of your Buy List)
        # Filter only the tickers that are actually in the downloaded data
        # Check intersection with columns
        valid_tickers = [t for t in self.tickers if t in data.columns]
        
        if not valid_tickers:
            print("❌ No valid stock data found to calculate strategy.")
            return

        strategy_col = normalized_data[valid_tickers].mean(axis=1)
        
        benchmark_col = None
        if '^NSEI' in normalized_data.columns:
            benchmark_col = normalized_data['^NSEI']
        else:
            print("⚠ Benchmark (^NSEI) missing. Skipping comparison.")

        # Calculate Final Returns
        strategy_return = strategy_col.iloc[-1] - 100
        
        print("\n--- 📊 RESULTS ---")
        print(f"Timeframe: {start_date} to {end_date}")
        print(f"Strategy Return:   {strategy_return:.2f}%")
        
        if benchmark_col is not None:
            benchmark_return = benchmark_col.iloc[-1] - 100
            print(f"NIFTY 50 Return:   {benchmark_return:.2f}%")
            
            diff = strategy_return - benchmark_return
            if strategy_return > benchmark_return:
                print(f"✅ SUCCESS: You beat the market by {diff:.2f}%! 🚀")
            else:
                print(f"❌ UNDERPERFORMANCE: Strategy lagged by {abs(diff):.2f}%.")

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(strategy_col, label='Your Strategy (Equal Weight)', linewidth=2, color='green')
        
        if benchmark_col is not None:
            plt.plot(benchmark_col, label='NIFTY 50 Benchmark', linewidth=2, color='gray', linestyle='--')
        
        plt.title(f"Backtest: Strategy vs NIFTY 50 ({self.years} Years)")
        plt.xlabel('Date')
        plt.ylabel('Growth of ₹100')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        output_file = 'reports/backtest_results.png'
        plt.savefig(output_file)
        print(f"\n📈 Chart saved to: {output_file}")

if __name__ == "__main__":
    # Point it to your generated buy list
    bt = Backtester('reports/NSE_Buy_List.csv', years=3)
    bt.run_backtest()