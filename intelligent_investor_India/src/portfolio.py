import pandas as pd
import math
from config.settings import DATA_DIR

class PortfolioManager:
    def __init__(self, total_capital):
        self.capital = float(total_capital)
        self.holdings = self.load_holdings()

    def load_holdings(self):
        """
        Loads current portfolio from data/holdings.csv
        Robustly handles encoding errors (Excel formats).
        """
        path = DATA_DIR / "holdings.csv"
        
        if not path.exists():
            print("⚠ No holdings.csv found. Assuming empty portfolio.")
            return pd.DataFrame(columns=['Ticker', 'Shares', 'AvgPrice', 'Type'])

        try:
            # Try 1: Standard UTF-8
            df = pd.read_csv(path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Try 2: Windows/Excel format (cp1252)
                print("⚠ CSV Encoding issue detected. Retrying with 'cp1252' (Excel format)...")
                df = pd.read_csv(path, encoding='cp1252')
            except Exception:
                try:
                    # Try 3: Latin1 (Old standard)
                    df = pd.read_csv(path, encoding='latin1')
                except Exception as e:
                    print(f"❌ Critical Error: Could not read holdings.csv. {e}")
                    return pd.DataFrame(columns=['Ticker', 'Shares', 'AvgPrice', 'Type'])
        
        # Normalize columns (Strip whitespace)
        df.columns = df.columns.str.strip()
        
        print(f"✅ Loaded {len(df)} existing holdings.")
        return df

    def get_current_valuation(self):
        """
        Calculates the current value of existing holdings.
        """
        if self.holdings.empty:
            return 0, {}
        
        # Ensure numeric columns
        self.holdings['Shares'] = pd.to_numeric(self.holdings['Shares'], errors='coerce').fillna(0)
        self.holdings['AvgPrice'] = pd.to_numeric(self.holdings['AvgPrice'], errors='coerce').fillna(0)

        total_value = (self.holdings['Shares'] * self.holdings['AvgPrice']).sum()
        
        holdings_dict = {}
        for _, row in self.holdings.iterrows():
            holdings_dict[row['Ticker']] = row['Shares'] * row['AvgPrice']
            
        return total_value, holdings_dict

    def review_portfolio_for_sells(self, df_scored):
        """
        Checks current holdings against the new scores to find 'Sell' candidates.
        """
        if self.holdings.empty:
            return pd.DataFrame()

        print("\n--- 📉 PORTFOLIO REVIEW (Sell Check) ---")
        sell_orders = []

        for index, row in self.holdings.iterrows():
            ticker = row['Ticker']
            shares = row['Shares']
            avg_price = row['AvgPrice']
            type_asset = row['Type']

            # Skip ETFs/MFs
            if type_asset in ['MF', 'ETF', 'Index']:
                continue

            # Check if we have data
            if ticker not in df_scored.index:
                continue

            stats = df_scored.loc[ticker]
            current_price = stats['price']
            current_score = stats.get('total_score', 0)
            pe_ratio = stats.get('trailing_pe', 0)
            peg_ratio = stats.get('peg_ratio', 0)

            reason = ""
            
            # SELL RULES
            if current_score < 40:
                reason = f"Weak Fundamentals (Score: {current_score:.0f}/100)"
            elif pe_ratio > 80 and peg_ratio > 4.0:
                reason = f"Overvalued (P/E: {pe_ratio:.1f}, PEG: {peg_ratio:.1f})"

            if reason:
                profit_loss = (current_price - avg_price) / avg_price
                
                sell_orders.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'shares': shares,
                    'current_price': current_price,
                    'reason': reason,
                    'est_value': shares * current_price,
                    'pnl_pct': round(profit_loss * 100, 2)
                })

        return pd.DataFrame(sell_orders)

    def select_and_allocate(self, df_scored, top_n=5, max_sector_weight=0.30):
        current_pf_value, current_holdings = self.get_current_valuation()
        total_investment_pool = self.capital + current_pf_value
        
        print(f"\n--- PORTFOLIO CONTEXT ---")
        print(f"Existing Portfolio Value: ₹{current_pf_value:,.2f}")
        print(f"New Capital to Deploy:    ₹{self.capital:,.2f}")
        print(f"Total Combined Portfolio: ₹{total_investment_pool:,.2f}")

        recommendations = []

        # --- SAFETY BUCKET ---
        safe_assets = ['MF', 'ETF', 'Index']
        mf_holdings = self.holdings[self.holdings['Type'].isin(safe_assets)]
        
        current_mf_value = 0
        if not mf_holdings.empty:
            current_mf_value = (mf_holdings['Shares'] * mf_holdings['AvgPrice']).sum()
        
        target_mf_allocation = 0.20 * total_investment_pool
        mf_shortfall = target_mf_allocation - current_mf_value
        
        if mf_shortfall > 5000:
            print(f"\n⚠ Safety Shortfall: ₹{mf_shortfall:,.2f}")
            print(f"  👉 Allocating to Nifty BeES & Gold BeES")
            
            nifty_amt = mf_shortfall * 0.70
            gold_amt = mf_shortfall * 0.30
            
            if nifty_amt > 260:
                recommendations.append({
                    'ticker': 'NIFTYBEES.NS', 'sector': 'Index ETF',
                    'shares': math.floor(nifty_amt / 270), 'price': 270,
                    'est_cost': nifty_amt, 'allocation_pct': 0
                })
            
            if gold_amt > 60:
                recommendations.append({
                    'ticker': 'GOLDBEES.NS', 'sector': 'Commodity ETF',
                    'shares': math.floor(gold_amt / 62), 'price': 62,
                    'est_cost': gold_amt, 'allocation_pct': 0
                })
            
            self.capital -= mf_shortfall

        # --- STOCK ALLOCATION ---
        print(f"\n--- STOCK ALLOCATION (Remaining: ₹{self.capital:,.2f}) ---")
        
        score_col = 'total_score' if 'total_score' in df_scored.columns else 'score'
        df_sorted = df_scored.sort_values(by=score_col, ascending=False)
        
        target_per_stock = total_investment_pool / (top_n + len(current_holdings))
        target_per_stock = min(target_per_stock, self.capital / 3) 

        for ticker, row in df_sorted.iterrows():
            if self.capital < 2000:
                break
                
            existing_val = current_holdings.get(ticker, 0)
            if existing_val > target_per_stock * 0.8:
                print(f"  ⏭ Skipping {ticker}: Already hold ₹{existing_val:,.0f}")
                continue

            sector = row.get('sector', 'Unknown')
            price = row['price']
            
            if pd.isna(price) or price <= 0: continue

            amount_to_invest = target_per_stock - existing_val
            amount_to_invest = min(amount_to_invest, self.capital)
            
            shares = math.floor(amount_to_invest / price)
            cost = shares * price
            
            if shares > 0:
                recommendations.append({
                    'ticker': ticker,
                    'sector': sector,
                    'shares': shares,
                    'price': price,
                    'est_cost': cost,
                    'allocation_pct': round((cost / self.capital) * 100, 2)
                })
                self.capital -= cost
                print(f"  ✔ Buying {ticker} ({sector}) - ₹{cost:,.0f}")

        return pd.DataFrame(recommendations)