import pandas as pd

class InsuranceEngine:
    def __init__(self, profile):
        self.profile = profile
        self.annual_income = profile.get('monthly_income', 0) * 12

    def calculate_needs(self):
        """
        Calculates the Ideal Cover based on 2026 Financial Standards.
        """
        # --- 1. TERM INSURANCE (Life Cover) ---
        # Rule of Thumb: 15x to 20x of Annual Income
        required_term_cover = self.annual_income * 15
        
        # --- 2. HEALTH INSURANCE (Medical Cover) ---
        # Base Rule: ₹10 Lakhs minimum for Metro, ₹5 Lakhs for non-Metro
        # + ₹5 Lakhs per dependent
        base_health_cover = 1000000 # 10 Lakhs standard
        
        return {
            "term_cover_needed": required_term_cover,
            "health_cover_needed": base_health_cover
        }

    def get_recommendations(self):
        needs = self.calculate_needs()
        recommendations = []
        
        # --- TERM INSURANCE RECOMMENDATIONS (2026 Top Picks) ---
        if not self.profile.get('has_term_insurance'):
            cover_cr = needs['term_cover_needed'] / 10000000
            rec_text = f"Buy Term Insurance of ₹{cover_cr:.1f} Crores (15x Income)"
            
            recommendations.append({
                "Type": "Term Insurance",
                "Action": "MUST BUY",
                "Details": rec_text,
                "Top_Plan_1": "ICICI Pru iProtect Smart (Claim Ratio: 99.2%)",
                "Top_Plan_2": "HDFC Life Click 2 Protect (Comprehensive)",
                "Est_Premium": f"₹{12000 if self.profile.get('age') < 30 else 25000}/year"
            })
        
        # --- HEALTH INSURANCE RECOMMENDATIONS ---
        if not self.profile.get('has_health_insurance'):
            rec_text = f"Buy Health Cover of ₹{needs['health_cover_needed']/100000:.0f} Lakhs"
            
            recommendations.append({
                "Type": "Health Insurance",
                "Action": "MUST BUY",
                "Details": rec_text,
                "Top_Plan_1": "HDFC Ergo Optima Secure (2x Cover Benefit)",
                "Top_Plan_2": "Niva Bupa ReAssure 2.0 (Unlimited Refill)",
                "Est_Premium": f"₹{15000 if self.profile.get('age') < 30 else 25000}/year"
            })
            
            # Suggest Super Top-up for cheap extra cover
            recommendations.append({
                "Type": "Health Add-on",
                "Action": "Highly Recommended",
                "Details": "Buy Super Top-up of ₹50 Lakhs (Cheap Safety)",
                "Top_Plan_1": "Niva Bupa Health Recharge",
                "Top_Plan_2": "Care Enhance",
                "Est_Premium": "₹3,000/year"
            })

        return pd.DataFrame(recommendations)