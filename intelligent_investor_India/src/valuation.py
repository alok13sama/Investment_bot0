import pandas as pd
import numpy as np

class ValuationEngine:
    def __init__(self, df_fundamentals):
        self.df = df_fundamentals.copy()

    def clean_data(self):
        # 1. Fill Missing Values with "Safe" defaults
        numeric_cols = ['trailing_pe', 'forward_pe', 'price_to_book', 'roe', 
                        'profit_margin', 'debt_to_equity', 'peg_ratio', 'price']
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        self.df['trailing_pe'] = self.df['trailing_pe'].fillna(999)
        self.df['price_to_book'] = self.df['price_to_book'].fillna(999)
        self.df['roe'] = self.df['roe'].fillna(0)
        self.df['debt_to_equity'] = self.df['debt_to_equity'].fillna(999)
        
        # Ensure 'sector' column exists
        if 'sector' not in self.df.columns:
            self.df['sector'] = 'Unknown'
        else:
            self.df['sector'] = self.df['sector'].fillna('Unknown')
        
        return self.df

    def calculate_piotroski_f_score_lite(self, row):
        """
        Calculates a 'Lite' F-Score (0-5) based on available snapshot data.
        """
        score = 0
        # 1. Positive ROA (Profitability)
        if row['roe'] > 0: score += 1
        
        # 2. Positive Cash Flow (Proxy: Profit Margin > 0)
        if row['profit_margin'] > 0: score += 1
        
        # 3. Low Leverage (Debt < Equity)
        if row['debt_to_equity'] < 100: score += 1
        
        # 4. High Quality Earnings (PEG < 1.5)
        if row['peg_ratio'] < 1.5: score += 1
        
        return score 

    def score_valuation(self):
        self.df['value_score'] = 0
        self.df['quality_score'] = 0
        
        for index, row in self.df.iterrows():
            sector = str(row['sector']).lower()
            v_score = 0
            
            # --- SECTOR SPECIFIC LOGIC ---
            
            # 1. BANKS & FINANCE (Value P/B more than P/E)
            if 'financial' in sector or 'bank' in sector:
                if row['price_to_book'] < 1.5: v_score += 40
                elif row['price_to_book'] < 2.5: v_score += 20
                if row['roe'] > 0.12: v_score += 30
                v_score += 30 # Base score for stability

            # 2. REAL ESTATE / INFRA (High Debt is common)
            elif 'real estate' in sector or 'construction' in sector:
                if row['trailing_pe'] < 20: v_score += 40
                if row['debt_to_equity'] < 200: v_score += 30
                if row['profit_margin'] > 0.10: v_score += 30

            # 3. IT / TECH (High Margins, Debt Free)
            elif 'technology' in sector or 'services' in sector:
                if row['trailing_pe'] < 25: v_score += 30
                if row['debt_to_equity'] < 10: v_score += 30
                if row['profit_margin'] > 0.15: v_score += 40

            # 4. GENERAL MANUFACTURING
            else:
                if row['trailing_pe'] < 15: v_score += 40
                elif row['trailing_pe'] < 25: v_score += 20
                if row['debt_to_equity'] < 70: v_score += 30
                if row['roe'] > 0.15: v_score += 30

            self.df.at[index, 'value_score'] = v_score
            
            # --- QUALITY SCORE ---
            f_score = self.calculate_piotroski_f_score_lite(row)
            self.df.at[index, 'quality_score'] = (f_score / 4) * 100 

        return self.df

    def get_blended_score(self, tech_df=None):
        # --- FIX FOR OVERLAP ERROR ---
        # Instead of self.df.join(), we simply assign the columns if tech_df exists
        if tech_df is not None:
            if 'tech_score' in tech_df.columns:
                self.df['tech_score'] = tech_df['tech_score']
            if 'trend' in tech_df.columns:
                self.df['trend'] = tech_df['trend']
        
        # Ensure columns exist even if tech_df was None
        if 'tech_score' not in self.df.columns:
            self.df['tech_score'] = 0
            
        self.score_valuation()
        
        # FINAL WEIGHTED SCORE
        self.df['total_score'] = (
            (self.df['value_score'] * 0.4) + 
            (self.df['quality_score'] * 0.2) + 
            (self.df['tech_score'] * 0.4)
        )
        
        return self.df.sort_values(by='total_score', ascending=False)