import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SYMBOLS = ["MASPTOP50.NS", "MAHKTECH.NS", "AUTOBEES.NS", "GROWWEV.NS", "PHARMABEES.NS", "ITBEES.NS", "BANKIETF.NS"]

def get_returns(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1y")['Close']
        if data.empty: return None
        curr = data.iloc[-1]
        def calc(d):
            past = data.asof(data.index[-1] - timedelta(days=d))
            return round(((curr - past) / past) * 100, 2)
        return {"Symbol": symbol.replace(".NS",""), "LTP": round(curr,2), "1M %": calc(30), "3M %": calc(90), "6M %": calc(180), "1Y %": calc(365)}
    except: return None

def main():
    results = [get_returns(s) for s in SYMBOLS if get_returns(s)]
    df = pd.DataFrame(results).sort_values(by="1Y %", ascending=False)
    
    # Message formatting with FIXED CASE-SENSITIVE NAMES
    msg = f"<b>📅 ETF Screener ({datetime.now().strftime('%Y-%m-%d')})</b>\n\n"
    msg += "<code>Symbol      LTP    1Y%   6M%   3M%   1M%</code>\n"
    for _, row in df.iterrows():
        msg += f"<code>{row['Symbol']:<11} {row['LTP']:>6} {row['1Y %']:>5}% {row['6M %']:>5}% {row['3M %']:>5}% {row['1M %']:>5}%</code>\n"

    TOKEN = os.getenv('BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
