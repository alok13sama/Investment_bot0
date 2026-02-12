import pandas as pd

class MutualFundEngine:
    def __init__(self):
        # A curated list of top-performing funds for 2026
        # In a pro version, this would be fetched via API
        self.fund_universe = [
            {"name": "Parag Parikh Flexi Cap Fund", "category": "Core Equity", "risk": "Medium"},
            {"name": "UTI Nifty 50 Index Fund", "category": "Index", "risk": "Low"},
            {"name": "Quant Small Cap Fund", "category": "Aggressive", "risk": "High"},
            {"name": "SBI Liquid Fund", "category": "Debt", "risk": "Safe"},
            {"name": "HDFC Balanced Advantage Fund", "category": "Hybrid", "risk": "Medium"},
            {"name": "Nippon India Gold Savings Fund", "category": "Gold", "risk": "Safe"}
        ]

    def recommend_funds(self, allocation_dict, capital):
        """
        Allocates capital to MFs based on the user's profile split.
        """
        mf_capital = capital * (allocation_dict['Mutual_Funds'] / 100)
        safe_capital = capital * (allocation_dict['Safe_Debt_Gold'] / 100)
        
        recommendations = []
        
        print(f"\n--- 🏦 MUTUAL FUND ALLOCATION (₹{mf_capital + safe_capital:,.0f}) ---")
        
        # 1. CORE BUCKET (The Mutual Fund Allocation)
        # We split this 50-50 between an Index Fund and a Flexi Cap
        if mf_capital > 1000:
            amt = mf_capital / 2
            recommendations.append({"ticker": "UTI Nifty 50 Index", "type": "MF (Index)", "amount": amt})
            recommendations.append({"ticker": "Parag Parikh Flexi Cap", "type": "MF (Flexi)", "amount": amt})
            print(f"  ✔ Allocating ₹{amt:,.0f} to Index Fund (Stability)")
            print(f"  ✔ Allocating ₹{amt:,.0f} to Flexi Cap (Growth)")

        # 2. SAFE BUCKET (The Debt/Gold Allocation)
        # We split this 80-20 between Liquid Funds and Gold
        if safe_capital > 1000:
            debt_amt = safe_capital * 0.80
            gold_amt = safe_capital * 0.20
            
            recommendations.append({"ticker": "SBI Liquid Fund", "type": "MF (Debt)", "amount": debt_amt})
            recommendations.append({"ticker": "Nippon Gold Fund", "type": "MF (Gold)", "amount": gold_amt})
            print(f"  ✔ Allocating ₹{debt_amt:,.0f} to Liquid Fund (Emergency/Safe)")
            print(f"  ✔ Allocating ₹{gold_amt:,.0f} to Gold (Hedging)")

        return pd.DataFrame(recommendations)