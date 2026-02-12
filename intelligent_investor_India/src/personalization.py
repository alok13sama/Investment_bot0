import json
import os
from config.settings import DATA_DIR

class PersonalizationEngine:
    def __init__(self):
        self.profile = self.load_or_ask_profile()

    def load_or_ask_profile(self):
        path = DATA_DIR / "user_profile.json"
        
        # If file exists, load it
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        
        # If NOT, ask the user interactively
        print("\n👋 Hello! I need to know a bit about you to personalize your investments.")
        print("(I will save this for next time)")
        
        try:
            age = int(input("   > What is your Age? "))
            income = float(input("   > Monthly Income (₹)? "))
            expenses = float(input("   > Monthly Expenses (₹)? "))
            savings = float(input("   > Current Emergency Fund (₹)? "))
            
            print("\n   > How would you describe your Risk Appetite?")
            print("     1. Low (I hate losing money)")
            print("     2. Medium (I want balance)")
            print("     3. High (I want maximum growth)")
            risk_choice = input("   > Enter 1, 2, or 3: ")
            
            risk_map = {'1': 'Low', '2': 'Medium', '3': 'High'}
            risk_appetite = risk_map.get(risk_choice, 'Medium')

            profile = {
                "age": age,
                "monthly_income": income,
                "monthly_expenses": expenses,
                "current_emergency_fund": savings,
                "risk_appetite": risk_appetite,
                "has_term_insurance": False, # Default assumption
                "has_health_insurance": False
            }
            
            # Save it
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(profile, f, indent=4)
                
            return profile

        except ValueError:
            print("❌ Invalid input. Using default profile.")
            return {"age": 30, "risk_appetite": "Medium"}

    def get_asset_allocation(self):
        """
        Returns the % split between Stocks, Mutual Funds, and Gold
        Based on 'Rule of 100' (Equity % = 100 - Age)
        """
        age = self.profile.get('age', 30)
        risk = self.profile.get('risk_appetite', 'Medium')
        
        # Base Rule: 100 - Age = Equity Exposure
        equity_pct = 100 - age
        
        # Adjust for Risk Appetite
        if risk == 'High': equity_pct += 10
        if risk == 'Low': equity_pct -= 10
        
        # Cap limits
        equity_pct = max(20, min(equity_pct, 90))
        
        # The Rest goes to Debt/Gold (Safe)
        safe_pct = 100 - equity_pct
        
        # Split Equity: 
        # - Direct Stocks (Aggressive)
        # - Mutual Funds (Core Stability)
        if risk == 'High':
            stock_alloc = equity_pct * 0.70  # 70% of equity in Stocks
            mf_alloc = equity_pct * 0.30     # 30% of equity in MFs
        else:
            stock_alloc = equity_pct * 0.40  # Less risk = Less direct stocks
            mf_alloc = equity_pct * 0.60
            
        return {
            "Stocks": round(stock_alloc, 1),
            "Mutual_Funds": round(mf_alloc, 1),
            "Safe_Debt_Gold": round(safe_pct, 1)
        }