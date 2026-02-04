import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# 1. Securely get credentials from GitHub Secrets
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 2. List of your ETFs
ETFs = [
    "MASPTOP50.NS", 
    "MAHKTECH.NS", 
    "AUTOBEES.NS", 
    "GROWWEV.NS", 
    "PHARMABEES.NS", 
    "ITBEES.NS", 
    "BANKIETF.NS"
]

def calculate_return(current, historical):
    return round(((current - historical) / historical) * 100, 2)

def get_etf_data(ticker):
    try:
        # Fetching 1.5 years of data to ensure we have enough for the 1Y calculation
        data = yf.download(ticker, period="2y", interval="1d")
        if data.empty or len(data) < 260:
            return None
        
        # Get Close prices column
        close_prices = data['Close']
        ltp = float(close_prices.iloc[-1])
        
        # Calculate returns based on common trading day offsets
        # (Approx: 1W=5 days, 1M=21 days, 3M=63 days, 6M=126 days, 1Y=252 days)
        returns = {
            "ticker": ticker.replace(".NS", ""),
            "ltp": round(ltp, 2),
            "1W": calculate_return(ltp, float(close_prices.iloc[-5])),
            "1M": calculate_return(ltp, float(close_prices.iloc[-21])),
            "3M": calculate_return(ltp, float(close_prices.iloc[-63])),
            "6M": calculate_return(ltp, float(close_prices.iloc[-126])),
            "1Y": calculate_return(ltp, float(close_prices.iloc[-252]))
        }
        return returns
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def main():
    message = "📊 *ETF Performance Report* 🚀\n"
    message += "Format: LTP (1W | 1M | 3M | 6M | 1Y)\n\n"
    
    results = []
    for etf in ETFs:
        data = get_etf_data(etf)
        if data:
            results.append(data)
    
    # Sort by 1Y performance (Highest to Lowest)
    results.sort(key=lambda x: x['1Y'], reverse=True)

    for r in results:
        line = (f"*{r['ticker']}*: ₹{r['ltp']}\n"
                f"└ `{r['1W']}% | {r['1M']}% | {r['3M']}% | {r['6M']}% | {r['1Y']}%` \n\n")
        message += line
    
    message += "🕒 _Auto-generated via GitHub Actions_"
    
    if TOKEN and CHAT_ID:
        send_telegram_msg(message)
    else:
        print("Error: Credentials missing.")

if __name__ == "__main__":
    main()
