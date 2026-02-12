import json
import os
from config.settings import DATA_DIR

class FinancialHealth:
    def __init__(self):
        self.profile = self.load_profile()

    def load_profile(self):
        path = DATA_DIR / "user_profile.json"
        if not os.path.exists(path):
            print("⚠ No user_profile.json found. Using defaults.")
            return {
                "monthly_income": 0, "monthly_expenses": 0,
                "current_emergency_fund": 0, 
                "has_term_insurance": False, "has_health_insurance": False
            }
        
        with open(path, 'r') as f:
            return json.load(f)

    def check_health(self):
        """
        Analyzes financial health and returns a list of critical actions.
        """
        income = self.profile.get('monthly_income', 0)
        expenses = self.profile.get('monthly_expenses', 0)
        emergency_fund = self.profile.get('current_emergency_fund', 0)
        
        alerts = []
        status = "HEALTHY"
        
        print("\n--- 🏥 FINANCIAL HEALTH CHECK ---")
        
        # 1. Emergency Fund Check (Rule: 6 Months of Expenses)
        required_ef = expenses * 6
        if emergency_fund < required_ef:
            shortfall = required_ef - emergency_fund
            alerts.append({
                'priority': 'CRITICAL',
                'message': f"Emergency Fund Low! You need 6 months expenses (₹{required_ef:,.0f}). Shortfall: ₹{shortfall:,.0f}"
            })
            status = "CRITICAL"
        else:
            print(f"✔ Emergency Fund: Fully Funded (₹{emergency_fund:,.0f})")

        # 2. Insurance Check
        if not self.profile.get('has_term_insurance'):
            alerts.append({
                'priority': 'HIGH',
                'message': "No Term Insurance found. Please secure your family's future before aggressive investing."
            })
        
        if not self.profile.get('has_health_insurance'):
            alerts.append({
                'priority': 'HIGH',
                'message': "No Health Insurance found. One hospital bill can wipe out your portfolio."
            })

        # 3. Calculate Investable Surplus
        monthly_surplus = income - expenses
        print(f"✔ Monthly Surplus: ₹{monthly_surplus:,.0f} (Income - Expenses)")
        
        return status, monthly_surplus, alerts