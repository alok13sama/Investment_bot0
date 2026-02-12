import pandas as pd
from config.settings import STARTING_CAPITAL
from config.universe import get_nifty500_tickers
from src.data_loader import FundamentalLoader
from src.valuation import ValuationEngine
from src.portfolio import PortfolioManager
from src.sentiment import SentimentEngine
from src.history import HistoryEngine
from src.personalization import PersonalizationEngine
from src.mutual_funds import MutualFundEngine
from src.insurance import InsuranceEngine
from src.technical import TechnicalEngine 

pd.set_option('future.no_silent_downcasting', True)

def run_indian_bot():
    print("==========================================")
    print("   🇮🇳 INTELLIGENT INVESTOR: AI ADVISOR    ")
    print("==========================================")
    
    # --- 1. PERSONALIZE ---
    user_engine = PersonalizationEngine()
    allocation = user_engine.get_asset_allocation()
    profile = user_engine.profile
    
    print("\n📊 YOUR PERSONALIZED PLAN:")
    print(f"   Age: {profile.get('age')} | Risk: {profile.get('risk_appetite')}")
    
    # --- 2. INSURANCE CHECK (CRITICAL STEP) ---
    ins_engine = InsuranceEngine(profile)
    ins_recs = ins_engine.get_recommendations()
    
    current_capital = STARTING_CAPITAL
    
    if not ins_recs.empty:
        print("\n🚨 CRITICAL PROTECTION GAP DETECTED 🚨")
        print("Before investing in stocks, you MUST secure your family.")
        print(ins_recs[['Type', 'Details', 'Top_Plan_1', 'Est_Premium']].to_string(index=False))
        
        print("\n💡 Tip: Insurance protects your Wealth. Stocks only grow it.")
        proceed = input("Do you want to deduct estimated insurance premiums from your Investment Capital? (y/n): ")
        
        if proceed.lower() == 'y':
            total_premium = 0
            for item in ins_recs['Est_Premium']:
                 import re
                 nums = re.findall(r'\d+', str(item).replace(',', ''))
                 if nums: total_premium += int(nums[0])
            
            current_capital -= total_premium
            print(f"   ✔ Deducted ₹{total_premium:,} for Insurance. Remaining Capital: ₹{current_capital:,}")

    # --- 3. ASSET ALLOCATION ---
    print(f"\n   ---------------------------------------")
    print(f"   🎯 Stocks (Direct):      {allocation['Stocks']}%")
    print(f"   🎯 Mutual Funds (Core):  {allocation['Mutual_Funds']}%")
    print(f"   🎯 Debt & Gold (Safe):   {allocation['Safe_Debt_Gold']}%")
    
    stock_budget = current_capital * (allocation['Stocks'] / 100)
    
    if stock_budget <= 0:
        print("\n❌ No capital left for stocks after Insurance/Safety allocation.")
        return

    # --- 4. MUTUAL FUND EXECUTION ---
    mf_engine = MutualFundEngine()
    mf_orders = mf_engine.recommend_funds(allocation, current_capital)
    
    # --- 5. STOCK EXECUTION ---
    print(f"\n--- 📈 STOCK ALLOCATION (Budget: ₹{stock_budget:,.0f}) ---")
    
    # Load Universe & Holdings
    print("1. Loading Tickers & Holdings...")
    universe_tickers = get_nifty500_tickers()
    
    # (Optional: Load existing holdings here to avoid duplicates - skipped for brevity)
    
    print(f"2. Fetching Fundamentals for {len(universe_tickers)} stocks...")
    loader = FundamentalLoader(universe_tickers)
    df_raw = loader.get_key_stats()
    
    if not df_raw.empty:
        # --- A. Technical Analysis (Trend) ---
        print("\n3. Analyzing Trends & Valuation...")
        tech_engine = TechnicalEngine()
        df_tech = tech_engine.add_technical_indicators(df_raw)
        
        # --- B. Fundamental Analysis (Sector + Quality) ---
        val_engine = ValuationEngine(df_raw)
        val_engine.clean_data()
        df_scored = val_engine.get_blended_score(df_tech)
        
        # --- C. Portfolio Manager (Select Candidates) ---
        pm = PortfolioManager(stock_budget)
        
        # Sell Check (Optional)
        # if hasattr(pm, 'review_portfolio_for_sells'): ...
        
        # Get Candidates (Fetch top 15 to allow for filtering)
        candidates = pm.select_and_allocate(df_scored, top_n=15)
        
        if not candidates.empty:
            # --- D. History Check (Stability) ---
            hist = HistoryEngine()
            stable_buys = hist.filter_stocks(candidates)
            
            if not stable_buys.empty:
                # --- E. RSI Check (Timing) ---
                print("\n--- ⏱ RSI TIMING CHECK ---")
                rsi_approved = []
                for idx, row in stable_buys.iterrows():
                    ticker = row['ticker']
                    rsi = tech_engine.get_rsi(ticker)
                    
                    if rsi > 75:
                        print(f"  ❌ SKIPPED {ticker}: Overbought (RSI {rsi:.0f})")
                    elif rsi < 30:
                        print(f"  ✔ BUY SIGNAL {ticker}: Oversold (RSI {rsi:.0f})")
                        rsi_approved.append(idx)
                    else:
                        print(f"  ✔ Approved {ticker}: Neutral (RSI {rsi:.0f})")
                        rsi_approved.append(idx)
                
                timed_buys = stable_buys.loc[rsi_approved]
                
                # --- F. Sentiment Check (News) ---
                if not timed_buys.empty:
                    sent = SentimentEngine()
                    final_stock_buys = sent.filter_stocks(timed_buys)
                else:
                    final_stock_buys = pd.DataFrame()

                # --- 6. MERGE & REPORT ---
                print("\n==========================================")
                print("       🚀 FINAL INVESTMENT PLAN           ")
                print("==========================================")
                
                final_df = pd.DataFrame()
                
                # 1. Insurance
                if not ins_recs.empty:
                    print("\n--- 🛡️ STEP 1: PROTECTION (Execute Immediately) ---")
                    print(ins_recs[['Type', 'Details', 'Top_Plan_1']].to_string(index=False))
                    
                    ins_df = ins_recs[['Type', 'Details', 'Top_Plan_1']].rename(columns={'Details': 'Value', 'Top_Plan_1': 'Ticker'})
                    ins_df['Category'] = 'Insurance'
                    final_df = pd.concat([final_df, ins_df])

                # 2. Mutual Funds
                if not mf_orders.empty:
                    print("\n--- 🏦 STEP 2: MUTUAL FUNDS (SIP/Lumpsum) ---")
                    print(mf_orders[['ticker', 'type', 'amount']].to_string(index=False))
                    
                    mf_renamed = mf_orders.rename(columns={'ticker': 'Ticker', 'amount': 'Value'})
                    mf_renamed['Category'] = 'Mutual Fund'
                    final_df = pd.concat([final_df, mf_renamed[['Ticker', 'Value', 'Category']]])
                
                # 3. Stocks
                if not final_stock_buys.empty:
                    print("\n--- 📈 STEP 3: DIRECT STOCKS (Long Term) ---")
                    # Recalculate allocation based on final filtered list
                    # (Simple equal weight re-distribution of the stock budget)
                    final_count = len(final_stock_buys)
                    if final_count > 0:
                        #amt_per_stock = stock_budget / final_count
                        amt_per_stock = round(stock_budget / final_count, 2)
                        final_stock_buys['est_cost'] = amt_per_stock
                        final_stock_buys['shares'] = (amt_per_stock / final_stock_buys['price']).astype(int)

                    cols = ['ticker', 'sector', 'est_cost']
                    print(final_stock_buys[cols].to_string(index=False))
                    
                    st_renamed = final_stock_buys.rename(columns={'ticker': 'Ticker', 'est_cost': 'Value'})
                    st_renamed['Category'] = 'Stock'
                    final_df = pd.concat([final_df, st_renamed[['Ticker', 'Value', 'Category']]])
                
                # Save Report
                if not final_df.empty:
                    final_df.to_csv("reports/Final_Holistic_Plan.csv", index=False)
                    print(f"\n✔ Holistic Plan saved to: reports/Final_Holistic_Plan.csv")
                else:
                    print("\n❌ No investments recommended (All filters failed).")

if __name__ == "__main__":
    run_indian_bot()