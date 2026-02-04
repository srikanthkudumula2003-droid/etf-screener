import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SYMBOLS = ["MASPTOP50.NS", "MAHKTECH.NS", "AUTOBEES.NS", "GROWWEV.NS", "PHARMABEES.NS", "ITBEES.NS", "BANKIETF.NS"]

def get_returns(symbol):
    try:
        # Fetching 2 years of data for historical reference
        data = yf.Ticker(symbol).history(period="2y")['Close']
        if data.empty: return None
        
        curr = data.iloc[-1]
        prev_close = data.iloc[-2]
        
        def calc(days_back):
            target_date = data.index[-1] - timedelta(days=days_back)
            past = data.asof(target_date)
            ret = ((curr - past) / past) * 100
            # Return formatted string with color emoji
            emoji = "🟢" if ret >= 0 else "🔴"
            return f"{emoji}{round(ret, 2)}%"
        
        # Current Day Return logic
        day_ret = ((curr - prev_close) / prev_close) * 100
        day_emoji = "🟢" if day_ret >= 0 else "🔴"

        return {
            "Symbol": symbol.replace(".NS",""),
            "LTP": round(curr, 2),
            "Day": f"{day_emoji}{round(day_ret, 2)}%",
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
            
    if not results: return

    # Sorting by 1 Year returns
    df = pd.DataFrame(results).sort_values(by="1Y", ascending=False)
    
    # IST Time Fix (+5:30 hours from UTC server)
    ist_now = datetime.now() + timedelta(hours=5, minutes=30)
    
    msg = f"<b>📅 ETF Screener ({ist_now.strftime('%d-%m-%Y %H:%M')})</b>\n"
    msg += "<i>Format: LTP | Day | 1W | 1M | 3M | 6M | 1Y</i>\n\n"
    
    for _, row in df.iterrows():
        # Blue circle for LTP as requested
        msg += f"<b>{row['Symbol']}</b>: 🔵 ₹{row['LTP']}\n"
        msg += f"<code>↳ {row['Day']} | {row['1W']} | {row['1M']} | {row['3M']} | {row['6M']} | {row['1Y']}</code>\n\n"

    TOKEN = os.getenv('BOT_TOKEN')
    raw_ids = os.getenv('TELEGRAM_CHAT_ID') 
    
    if TOKEN and raw_ids:
        # Split IDs by comma to support both private chat and channel
        chat_ids = [id.strip() for id in raw_ids.split(',')]
        for chat_id in chat_ids:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
            requests.post(url, data=payload)

if __name__ == "__main__":
    main()
