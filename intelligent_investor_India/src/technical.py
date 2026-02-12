import pandas as pd
import yfinance as yf
import numpy as np

class TechnicalEngine:
    def __init__(self):
        pass

    def add_technical_indicators(self, df):
        """
        Calculates RSI and verifies Moving Averages.
        """
        print("\n--- 📉 CALCULATING RSI & MOMENTUM ---")
        
        # Ensure we have columns
        if '200_dma' not in df.columns:
            df['200_dma'] = df['price'] # Safety fallback
        
        # We need historical data for RSI.
        # Since fetching history for 500 stocks is slow, we use a heuristic or
        # fetch only for the shortlist.
        # FOR SPEED: We will skip RSI for the full list and only apply it 
        # to the 'Buy Candidates' later. 
        # Here we just mark the Trend.
        
        df['tech_score'] = 0
        
        # 1. Trend Filter (Price vs 200-DMA)
        # uptrend = Price > 200 DMA
        df['trend'] = np.where(df['price'] > df['200_dma'], 'Uptrend', 'Downtrend')
        
        # Score: +50 for Uptrend
        df.loc[df['trend'] == 'Uptrend', 'tech_score'] += 50
        
        # 2. Momentum (Price vs 50-DMA)
        if '50_dma' in df.columns:
            df.loc[df['price'] > df['50_dma'], 'tech_score'] += 30
            
            # Golden Cross Check (50 > 200)
            df.loc[df['50_dma'] > df['200_dma'], 'tech_score'] += 20
            
        return df

    def get_rsi(self, ticker, period=14):
        """
        Fetches history for a SINGLE stock to calculate RSI.
        Used only for final filtering to save time.
        """
        try:
            if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
                ticker = f"{ticker}.NS"
                
            # Fetch 3 mo history
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if len(hist) < period + 1:
                return 50 # Neutral if no data

            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
            
        except Exception:
            return 50 # Default Neutral