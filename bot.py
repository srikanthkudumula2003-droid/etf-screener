import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# The list of ETFs you are tracking
SYMBOLS = ["MASPTOP50.NS", "MAHKTECH.NS", "AUTOBEES.NS", "GROWWEV.NS", "PHARMABEES.NS", "ITBEES.NS", "BANKIETF.NS"]

def get_returns(symbol):
    try:
        # Fetching 2 years of data to ensure the 1Y back-calculation always has a reference point
        data = yf.Ticker(symbol).history(period="2y")['Close']
        if data.empty: return None
        
        curr = data.iloc[-1]
        
        def calc(days_back):
            # Finds the closest available trading price for the requested timeframe
            target_date = data.index[-1] - timedelta(days=days_back)
            past = data.asof(target_date)
            return round(((curr - past) / past) * 100, 2)
        
        return {
            "Symbol": symbol.replace(".NS",""),
            "LTP": round(curr, 2),
            "1W": calc(7),
            "1M": calc(30),
            "3M": calc(90),
            "6M": calc(180),
            "1Y": calc(365)
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def main():
    results = []
    for s in SYMBOLS:
        res = get_returns(s)
        if res:
            results.append(res)
            
    if not results:
        print("No data found.")
        return

    # Sorting the list so the best performing ETF for the year is at the top
    df = pd.DataFrame(results).sort_values(by="1Y", ascending=False)
    
    # --- IST TIME FIX ---
    # GitHub servers use UTC; we add 5 hours and 30 minutes to match Indian Standard Time
    ist_now = datetime.now() + timedelta(hours=5, minutes=30)
    
    msg = f"<b>📅 ETF Screener ({ist_now.strftime('%d-%m-%Y %H:%M')})</b>\n"
    msg += "<i>Format: LTP | 1W | 1M | 3M | 6M | 1Y</i>\n\n"
    
    for _, row in df.iterrows():
        msg += f"<b>{row['Symbol']}</b>: ₹{row['LTP']}\n"
        msg += f"<code>↳ {row['1W']}% | {row['1M']}% | {row['3M']}% | {row['6M']}% | {row['1Y']}%</code>\n\n"

    # Telegram Credentials from GitHub Secrets
    TOKEN = os.getenv('BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload)
    else:
        print("Error: BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment.")

if __name__ == "__main__":
    main()
