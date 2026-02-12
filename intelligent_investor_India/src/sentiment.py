import yfinance as yf
from textblob import TextBlob
import time

class SentimentEngine:
    def __init__(self):
        pass

    def get_news_sentiment(self, ticker):
        """
        Fetches latest news and returns a sentiment score (-1 to +1).
        """
        try:
            # Add .NS suffix if missing
            if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
                ticker = f"{ticker}.NS"

            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print(f"  ℹ No recent news found for {ticker}. Assuming Neutral.")
                return 0, []

            total_polarity = 0
            count = 0
            headlines = []

            for item in news_list[:5]: # Check last 5 headlines
                title = item.get('title', '')
                if not title: continue
                
                # Analyze Sentiment
                analysis = TextBlob(title)
                polarity = analysis.sentiment.polarity
                
                total_polarity += polarity
                count += 1
                headlines.append(f"{title} ({polarity:.2f})")

            if count == 0:
                return 0, []

            avg_score = total_polarity / count
            return avg_score, headlines

        except Exception as e:
            print(f"  ⚠ Error fetching news for {ticker}: {e}")
            return 0, []

    def filter_stocks(self, df_recommendations):
        """
        Takes the Buy List and removes stocks with BAD news.
        """
        if df_recommendations.empty:
            return df_recommendations

        print("\n--- 📰 NEWS SENTIMENT CHECK ---")
        approved_indices = []

        for index, row in df_recommendations.iterrows():
            ticker = row['ticker']
            print(f"  > Scanning news for {ticker}...")
            
            score, headlines = self.get_news_sentiment(ticker)
            
            # RULE: If score is below -0.15, it's negative news.
            if score < -0.15:
                print(f"  ❌ BLOCKED {ticker}: Negative Sentiment ({score:.2f})")
                print(f"     Headline: {headlines[0]}") # Show the bad news
            else:
                status = "Positive" if score > 0.1 else "Neutral"
                print(f"  ✔ Approved {ticker}: {status} ({score:.2f})")
                approved_indices.append(index)
            
            # Sleep briefly to avoid blocking by API
            time.sleep(0.5)

        return df_recommendations.loc[approved_indices]