import yfinance as yf
import pandas as pd

class FundamentalLoader:
    def __init__(self, tickers):
        self.tickers = tickers

    def get_key_stats(self):
        data = []
        print(f"--- Fetching data for {len(self.tickers)} stocks... ---")

        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # --- HELPER: Manual PEG Calculation ---
                trailing_pe = info.get('trailingPE')
                forward_pe = info.get('forwardPE')
                peg_ratio = info.get('pegRatio')

                if (peg_ratio is None) and (trailing_pe and forward_pe):
                    try:
                        if forward_pe < trailing_pe:
                            growth_rate = (trailing_pe / forward_pe) - 1
                            if growth_rate > 0.05: 
                                peg_ratio = trailing_pe / (growth_rate * 100)
                    except:
                        pass

                stock_data = {
                    'ticker': ticker,
                    'sector': info.get('sector', 'Unknown'),
                    'price': info.get('currentPrice'),
                    'market_cap': info.get('marketCap'),
                    
                    # --- TECHNICALS (CRITICAL PART) ---
                    '200_dma': info.get('twoHundredDayAverage'),
                    '50_dma': info.get('fiftyDayAverage'),
                    
                    'trailing_pe': trailing_pe,
                    'forward_pe': forward_pe,
                    'peg_ratio': peg_ratio,
                    'price_to_book': info.get('priceToBook'),
                    'roe': info.get('returnOnEquity'),
                    'profit_margin': info.get('profitMargins'),
                    'debt_to_equity': info.get('debtToEquity'),
                    'current_ratio': info.get('currentRatio'),
                    'dividend_yield': info.get('dividendYield'),
                    'target_mean_price': info.get('targetMeanPrice')
                }
                
                data.append(stock_data)
                print(f"✔ Processed {ticker}")                
            except Exception as e:
                print(f"❌ Error fetching {ticker}: {e}")

        df = pd.DataFrame(data)
        
        # --- DEBUG PRINT: Prove the columns exist ---
        if not df.empty:
            print("\n🔍 DEBUG: Columns found in data:")
            print(df.columns.tolist()) 
            df.set_index('ticker', inplace=True)
            
        return df