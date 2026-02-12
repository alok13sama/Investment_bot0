import os
import pandas as pd
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load secrets
load_dotenv()

class ExecutionEngine:
    def __init__(self):
        """
        Initializes connection to Alpaca Paper Trading.
        """
        self.api = tradeapi.REST(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            os.getenv("ALPACA_ENDPOINT"),
            api_version='v2'
        )
        
        # Check connection
        try:
            account = self.api.get_account()
            print(f"✅ Connected to Alpaca! Buying Power: ${account.buying_power}")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

    def execute_orders(self, csv_path):
        """
        Reads the CSV report and places orders.
        """
        try:
            orders_df = pd.read_csv(csv_path)
        except FileNotFoundError:
            print("⚠ No order file found. Run main.py first.")
            return

        if orders_df.empty:
            print("⚠ Order file is empty.")
            return

        print(f"\n--- Executing {len(orders_df)} Orders ---")

        for index, row in orders_df.items():
            # Note: If reading from CSV, iterate differently or ensure correct iteration
            # Let's fix the iteration for DataFrame
            pass 
        
        # Correct iteration loop
        for index, row in orders_df.iterrows():
            ticker = row['ticker']
            qty = int(row['shares'])
            
            if qty <= 0:
                continue
                
            print(f"🚀 Placing Order: Buy {qty} shares of {ticker}...")
            
            try:
                self.api.submit_order(
                    symbol=ticker,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                print(f"   ✔ Order Sent: {ticker}")
            except Exception as e:
                print(f"   ❌ Order Failed for {ticker}: {e}")

if __name__ == "__main__":
    # Test the execution independently
    exe = ExecutionEngine()
    # exe.execute_orders("reports/final_buy_orders.csv") # Uncomment to test for real