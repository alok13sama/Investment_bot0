import pandas as pd
import matplotlib.pyplot as plt
import os

# Define file paths
HOLDINGS_PATH = 'data/holdings.csv'
BUY_LIST_PATH = 'reports/NSE_Buy_List.csv'
OUTPUT_IMAGE = 'reports/portfolio_allocation.png'

def generate_portfolio_chart():
    print("--- Generating Portfolio Visualization ---")

    # 1. Load Existing Holdings
    df_holdings = pd.DataFrame()
    if os.path.exists(HOLDINGS_PATH):
        try:
            df_holdings = pd.read_csv(HOLDINGS_PATH)
            # Calculate current value (Shares * Price)
            # Note: Ensure your CSV has 'Shares' and 'AvgPrice' (or 'CurrentPrice')
            price_col = 'CurrentPrice' if 'CurrentPrice' in df_holdings.columns else 'AvgPrice'
            df_holdings['Value'] = df_holdings['Shares'] * df_holdings[price_col]
            df_holdings['Source'] = 'Existing Holding'
            print(f"✅ Loaded {len(df_holdings)} existing holdings.")
        except Exception as e:
            print(f"❌ Error loading holdings: {e}")
    
    # 2. Load New Buy Recommendations
    df_buys = pd.DataFrame()
    if os.path.exists(BUY_LIST_PATH):
        try:
            df_buys = pd.read_csv(BUY_LIST_PATH)
            # Standardize columns (The buy list uses lowercase 'ticker', 'est_cost')
            df_buys = df_buys.rename(columns={'ticker': 'Ticker', 'est_cost': 'Value'})
            df_buys['Source'] = 'New Buy'
            print(f"✅ Loaded {len(df_buys)} new buy recommendations.")
        except Exception as e:
            print(f"❌ Error loading buy list: {e}")

    # 3. Combine Data
    if df_holdings.empty and df_buys.empty:
        print("⚠ No data found to visualize.")
        return

    # Select only necessary columns
    cols = ['Ticker', 'Value', 'Source']
    df_combined = pd.concat([
        df_holdings[cols] if not df_holdings.empty else pd.DataFrame(), 
        df_buys[cols] if not df_buys.empty else pd.DataFrame()
    ], ignore_index=True)

    # Group by Ticker (in case you are buying more of a stock you already own)
    df_final = df_combined.groupby('Ticker', as_index=False)['Value'].sum()
    
    # Calculate Total Portfolio Value
    total_value = df_final['Value'].sum()
    df_final['Percent'] = (df_final['Value'] / total_value) * 100
    
    # Sort large to small
    df_final = df_final.sort_values(by='Value', ascending=False)

    # 4. Generate Donut Chart
    plt.figure(figsize=(12, 8))
    
    # Create labels (Ticker + %)
    # Only label slices bigger than 2% to avoid clutter
    labels = [
        f"{row['Ticker']}\n({row['Percent']:.1f}%)" if row['Percent'] > 2 else "" 
        for _, row in df_final.iterrows()
    ]
    
    # Color map
    colors = plt.cm.tab20c.colors
    
    wedges, texts, autotexts = plt.pie(
        df_final['Value'], 
        labels=labels,
        autopct='', # We used custom labels above
        startangle=140,
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w') # Width controls the "Donut" hole size
    )
    
    # Add Center Text
    plt.text(0, 0, f"Total Value\n₹{total_value:,.0f}", ha='center', va='center', fontsize=14, fontweight='bold')
    
    plt.title("Projected Portfolio Allocation\n(Holdings + New Buys)", fontsize=16)
    plt.tight_layout()
    
    # Save
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"\n✔ Chart saved to: {OUTPUT_IMAGE}")
    
    # 5. Print Summary Table
    print("\n--- Allocation Summary ---")
    print(df_final[['Ticker', 'Value', 'Percent']].head(10).to_string(index=False))

if __name__ == "__main__":
    generate_portfolio_chart()