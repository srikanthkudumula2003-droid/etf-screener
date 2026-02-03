import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Add your ETF symbols here (must end in .NS for NSE)
SYMBOLS = [
    "MASPTOP50.NS", "MAHKTECH.NS", "AUTOBEES.NS", 
    "GROWWEV.NS", "PHARMABEES.NS", "ITBEES.NS", "BANKIETF.NS"
]

def get_returns(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # Fetch 1 year of data to calculate all periods
        data = ticker.history(period="1y")['Close']
        if data.empty: return None
        
        current_price = data.iloc[-1]
        
        # Helper to find price closest to N days ago
        def calc_pct(days):
            target_date = data.index[-1] - timedelta(days=days)
            # Find the closest trading day
            price_n_days_ago = data.asof(target_date)
            return ((current_price - price_n_days_ago) / price_n_days_ago) * 100

        return {
            "Symbol": symbol.replace(".NS", ""),
            "LTP": round(current_price, 2),
            "1M %": round(calc_pct(30), 2),
            "3M %": round(calc_pct(90), 2),
            "6M %": round(calc_pct(180), 2),
            "1Y %": round(calc_pct(365), 2)
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def main():
    results = []
    for s in SYMBOLS:
        data = get_returns(s)
        if data: results.append(data)
    
    # Create DataFrame and sort by 1-Year returns (Descending)
    df = pd.DataFrame(results)
    df = df.sort_values(by="1Y %", ascending=False)
    
    # Format message for Telegram
    msg = f"<b>📅 ETF Screener Update ({datetime.now().strftime('%Y-%m-%d')})</b>\n\n"
    msg += "<code>Symbol      LTP    1Y%    6M% 3m% 1m%</code>\n"
    for _, row in df.iterrows():
        msg += f"<code>{row['Symbol']:<11} {row['LTP']:>6} {row['1Y %']:>6}% 
        {row['6M %']:>6}% {row['3M %']:>6}% {row['1M %']:>6}%</code>\n"

    # Send via Telegram
    TOKEN = os.getenv('BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
