import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SYMBOLS = ["MASPTOP50.NS", "MAHKTECH.NS", "AUTOBEES.NS", "GROWWEV.NS", "PHARMABEES.NS", "ITBEES.NS", "BANKIETF.NS"]

def get_returns(symbol):
    try:
        # Fetch 1y data to ensure we have historical prices
        data = yf.Ticker(symbol).history(period="1y")['Close']
        if data.empty: return None
        
        curr = data.iloc[-1]
        
        def calc(days_back):
            # Find the price closest to the target date
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
    # Filter out None results
    results = []
    for s in SYMBOLS:
        res = get_returns(s)
        if res:
            results.append(res)
            
    if not results:
        print("No data found.")
        return

    # Create DataFrame and Sort by 1 Year returns
    df = pd.DataFrame(results).sort_values(by="1Y", ascending=False)
    
    # Message formatting using HTML for a clean table look
    msg = f"<b>📅 ETF Screener ({datetime.now().strftime('%d-%m-%Y %H:%M')})</b>\n"
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
        print("Error: BOT_TOKEN or TELEGRAM_CHAT_ID not set in Environment.")

if __name__ == "__main__":
    main()
