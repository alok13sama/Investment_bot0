import streamlit as st
import pandas as pd
import plotly.express as px
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

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Intelligent Investor AI", page_icon="🇮🇳", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .stButton>button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: USER INPUTS ---
st.sidebar.title("👤 User Profile")
age = st.sidebar.number_input("Age", min_value=18, max_value=80, value=30)
income = st.sidebar.number_input("Monthly Income (₹)", min_value=0, value=100000, step=5000)
savings = st.sidebar.number_input("Emergency Fund (₹)", min_value=0, value=200000, step=10000)
risk_appetite = st.sidebar.select_slider("Risk Appetite", options=["Low", "Medium", "High"], value="Medium")

st.sidebar.markdown("---")
st.sidebar.title("💰 Investment")
capital = st.sidebar.number_input("Capital to Deploy (₹)", min_value=10000, value=100000, step=5000)
deduct_insurance = st.sidebar.checkbox("Deduct Insurance Premiums?", value=True)

run_btn = st.sidebar.button("🚀 RUN AI ANALYSIS")

# --- CACHED FUNCTIONS (Speed Up) ---
@st.cache_data
def load_market_data():
    tickers = get_nifty500_tickers()
    loader = FundamentalLoader(tickers)
    return loader.get_key_stats()

# --- MAIN APP LOGIC ---
st.title("🇮🇳 Intelligent Investor: AI Wealth Manager")
st.markdown("Your personal robo-advisor for Stocks, Mutual Funds, and Insurance.")

if run_btn:
    # 1. PROFILE & ALLOCATION
    profile = {
        "age": age,
        "monthly_income": income,
        "current_emergency_fund": savings,
        "risk_appetite": risk_appetite,
        "has_term_insurance": False,
        "has_health_insurance": False
    }
    
    # Calculate Allocation
    user_engine = PersonalizationEngine() 
    user_engine.profile = profile # Override with sidebar inputs
    allocation = user_engine.get_asset_allocation()

    # 2. INSURANCE CHECK
    ins_engine = InsuranceEngine(profile)
    ins_recs = ins_engine.get_recommendations()
    
    # Adjust Capital
    adjusted_capital = capital
    if deduct_insurance and not ins_recs.empty:
        est_premium = 0
        for item in ins_recs['Est_Premium']:
            import re
            nums = re.findall(r'\d+', str(item).replace(',', ''))
            if nums: est_premium += int(nums[0])
        adjusted_capital -= est_premium

    # 3. TABS LAYOUT
    tab1, tab2, tab3 = st.tabs(["🛡️ Financial Health", "📊 Asset Allocation", "📈 Stock Analysis"])

    with tab1:
        st.header("Financial Health Check")
        
        # Emergency Fund
        req_ef = income * 6
        col1, col2 = st.columns(2)
        col1.metric("Emergency Fund", f"₹{savings:,.0f}", delta=f"{savings-req_ef:,.0f} Shortfall" if savings < req_ef else "Fully Funded")
        
        # Insurance Alerts
        if not ins_recs.empty:
            st.error("🚨 Critical Protection Gap Detected!")
            for i, row in ins_recs.iterrows():
                with st.container():
                    st.markdown(f"**{row['Type']}**: {row['Details']}")
                    st.info(f"Recommended: {row['Top_Plan_1']} (~{row['Est_Premium']})")
        else:
            st.success("✅ Your Insurance Coverage looks good!")

    with tab2:
        st.header("Smart Asset Allocation")
        
        # Donut Chart
        alloc_data = pd.DataFrame({
            "Asset": allocation.keys(),
            "Percentage": allocation.values()
        })
        fig = px.pie(alloc_data, values='Percentage', names='Asset', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig)
        
        # Mutual Fund Recs
        st.subheader("🏦 Mutual Fund Recommendations")
        mf_engine = MutualFundEngine()
        mf_orders = mf_engine.recommend_funds(allocation, adjusted_capital)
        st.dataframe(mf_orders, hide_index=True, use_container_width=True)

    with tab3:
        st.header("AI Stock Picker (NIFTY 500)")
        
        stock_budget = adjusted_capital * (allocation['Stocks'] / 100)
        st.info(f"Allocating ₹{stock_budget:,.0f} to Direct Stocks based on Valuation & Momentum.")
        
        with st.spinner("Scanning 500 stocks... (This takes 30-60s)"):
            df_raw = load_market_data()
            
            if not df_raw.empty:
                # Analysis Pipeline
                tech_engine = TechnicalEngine()
                df_tech = tech_engine.add_technical_indicators(df_raw)
                
                val_engine = ValuationEngine(df_raw)
                val_engine.clean_data()
                df_scored = val_engine.get_blended_score(df_tech)
                
                pm = PortfolioManager(stock_budget)
                candidates = pm.select_and_allocate(df_scored, top_n=15)
                
if not candidates.empty:
                    # History & Sentiment
                    hist = HistoryEngine()
                    stable = hist.filter_stocks(candidates)
                    
                    # Display Final Table
                    st.subheader("🏆 Top AI Picks")
                    
                    # --- FIX: ROBUST MERGE ---
                    # 1. Ensure 'ticker' is a column in df_scored (reset index if needed)
                    if 'ticker' not in df_scored.columns:
                        df_scored = df_scored.reset_index()
                        if 'index' in df_scored.columns: # Rename generic 'index' to 'ticker'
                            df_scored = df_scored.rename(columns={'index': 'ticker'})

                    # 2. Define the columns we WANT
                    desired_cols = ['ticker', 'sector', 'total_score', 'value_score', 'tech_score']
                    
                    # 3. Find which of these actually EXIST in df_scored
                    available_cols = [c for c in desired_cols if c in df_scored.columns]
                    
                    # 4. Merge only the available data
                    # We use a suffix to avoid "value_score_x" and "value_score_y" confusion
                    if 'ticker' in stable.columns and 'ticker' in df_scored.columns:
                        stable = pd.merge(stable, df_scored[available_cols], on='ticker', how='left', suffixes=('', '_new'))
                        
                        # Fill generic N/A for missing scores so app doesn't crash
                        for col in ['total_score', 'value_score', 'tech_score']:
                            if col in stable.columns:
                                stable[col] = stable[col].fillna(0)
                            else:
                                stable[col] = 0 # Create dummy column if merge failed entirely

                    # 5. Create Display DF safely
                    display_cols = ['ticker', 'price', 'total_score', 'value_score', 'tech_score']
                    if 'sector' in stable.columns:
                        display_cols.insert(1, 'sector')
                        
                    display_df = stable[display_cols].copy()
                    
                    # Format
                    display_df['price'] = display_df['price'].apply(lambda x: f"₹{x:,.2f}")
                    display_df['total_score'] = display_df['total_score'].astype(int)
                    
                    st.dataframe(display_df.style.background_gradient(subset=['total_score'], cmap='Greens'), use_container_width=True)
                    
                    # Sentiment Check for Top 3
                    st.subheader("📰 News Sentiment Audit (Top Picks)")
                    sent = SentimentEngine()
                    final_buys = sent.filter_stocks(stable.head(5))
                    
                    for i, row in final_buys.iterrows():
                         st.success(f"✔ {row['ticker']}: Sentiment Neutral/Positive (Safe to Buy)")
                    else:
                         st.warning("No stocks met the strict buying criteria today.")
                    else:
                         st.error("Failed to fetch market data.")

else:

    st.info("👈 Enter your details in the Sidebar and click 'RUN AI ANALYSIS' to start.")


