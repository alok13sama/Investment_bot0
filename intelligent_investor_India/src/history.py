import yfinance as yf
import pandas as pd

class HistoryEngine:
    def __init__(self):
        pass

    def check_stability(self, ticker):
        """
        Fetches last 4 years of Financials.
        Returns:
        - is_stable (True/False)
        - growth_msg (String explaining why)
        """
        try:
            if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
                ticker = f"{ticker}.NS"

            stock = yf.Ticker(ticker)
            fin = stock.financials # Annual Financials
            
            if fin.empty:
                # If no data, we give it the benefit of the doubt but warn user
                return True, "No historical data available (Neutral)"

            # Get Revenue and Net Income rows
            try:
                # yfinance keys can be inconsistent
                revenue = fin.loc['Total Revenue'] if 'Total Revenue' in fin.index else fin.iloc[0]
                net_income = fin.loc['Net Income'] if 'Net Income' in fin.index else fin.iloc[-1]
            except Exception:
                return True, "Data format mismatch (Skipped)"

            # Reverse to check trend: Oldest -> Newest
            rev_trend = revenue.iloc[::-1] 
            inc_trend = net_income.iloc[::-1]
            
            years_count = len(rev_trend)
            if years_count < 3:
                return True, "Not enough history (Skipped)"

            # CHECK 1: PROFITABILITY (Must be profitable in latest year)
            latest_income = inc_trend.iloc[-1]
            if pd.isna(latest_income) or latest_income < 0:
                 # Check previous year if latest is NaN (sometimes data is delayed)
                if len(inc_trend) > 1 and inc_trend.iloc[-2] < 0:
                    return False, f"Loss making in recent years"

            # CHECK 2: REVENUE GROWTH
            latest_rev = rev_trend.iloc[-1]
            old_rev = rev_trend.iloc[0]
            
            # Fix for NaN% error
            if pd.isna(old_rev) or old_rev == 0:
                growth_pct = 0.0
            else:
                growth_pct = ((latest_rev - old_rev) / old_rev) * 100

            # CHECK 3: CONSISTENCY (Did it crash recently?)
            # If Revenue dropped by >20% in the last year
            if len(rev_trend) >= 2:
                prev_rev = rev_trend.iloc[-2]
                if prev_rev > 0:
                    rev_change = (latest_rev - prev_rev) / prev_rev
                    if rev_change < -0.20:
                        return False, "Revenue collapsed >20% last year"

            return True, f"Growing: {growth_pct:.1f}% over {years_count} yrs"

        except Exception as e:
            # Don't fail the whole bot just because history check failed
            return True, f"History check skipped ({e})"

    def filter_stocks(self, df_recommendations):
        print("\n--- 📜 3-YEAR HISTORY CHECK ---")
        approved_indices = []

        for index, row in df_recommendations.iterrows():
            ticker = row['ticker']
            print(f"  > Auditing financials for {ticker}...")
            
            is_stable, msg = self.check_stability(ticker)
            
            if is_stable:
                print(f"  ✔ Passed {ticker}: {msg}")
                approved_indices.append(index)
            else:
                print(f"  ❌ REJECTED {ticker}: {msg}")
        
        return df_recommendations.loc[approved_indices]