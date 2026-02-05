import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# The 7 ETFs you are tracking
SYMBOLS = [
    "MASPTOP50.NS", 
    "MAHKTECH.NS", 
    "AUTOBEES.NS", 
    "GROWWEV.NS", 
    "PHARMABEES.NS", 
    "ITBEES.NS", 
    "BANKIETF.NS"
]

def get_returns(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # Fetching 2 years of data to ensure 1Y returns and 52W High are accurate
        data = ticker.history(period="2y")['Close']
        info = ticker.info
        
        if data.empty:
            return None
        
        curr = data.iloc[-1]
        
        # 52-Week High Calculation (uses ticker info or fallback to max of last 252 trading days)
        high_52w = info.get('fiftyTwoWeekHigh', max(data.iloc[-252:]))
        dist_from_high = ((curr - high_52w) / high_52w) * 100
        
        # Function to calculate point-to-point returns
        def calc_ret(days_back):
            target_date = data.index[-1] - timedelta(days=days_back)
            past_price = data.asof(target_date)
            ret = ((curr - past_price) / past_price) * 100
            emoji = "🟢" if ret >= 0 else "🔴"
            return f"{emoji}{round(ret, 1)}%"
        
        # Daily Return (LTP vs Previous Close)
        prev_close = data.iloc[-2]
        day_ret = ((curr - prev_close) / prev_close) * 100
        day_emoji = "🟢" if day_ret >= 0 else "🔴"

        return {
            "Symbol": symbol.replace(".NS", ""),
            "LTP": round(curr, 2),
            "DayNum": day_ret, # Used for identifying the Top Gainer
            "Day": f"{day_emoji}{round(day_ret, 1)}%",
            "1W": calc_ret(7),
            "1M": calc_ret(30),
            "3M": calc_ret(90),
            "6M": calc_ret(180),
            "1Y": calc_ret(365),
            "52W_Dist": f"{round(dist_from_high, 1)}%"
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def main():
    # 1. Fetch data for all symbols
    results = [get_returns(s) for s in SYMBOLS if get_returns(s)]
    
    if not results:
        print("No data fetched. Check internet or symbols.")
        return

    # 2. Sort results by 1-Year return (Descending)
    df = pd.DataFrame(results).sort_values(by="1Y", ascending=False)
    
    # 3. Identify the Top Gainer of the day
    top_gainer_symbol = df.sort_values(by="DayNum", ascending=False).iloc[0]['Symbol']
    
    # 4. Calculate Market Sentiment
    green_count = sum(1 for r in results if "🟢" in r['Day'])
    sentiment = "🚀 BULLISH" if green_count > len(results)/2 else "📉 BEARISH"

    # 5. Get IST Time
    ist_now = datetime.now() + timedelta(hours=5, minutes=30)
    
    # --- MESSAGE BUILDING ---
    msg = f"<b>📊 ETF PERFORMANCE INSIGHTS</b>\n"
    msg += f"📅 <i>{ist_now.strftime('%d-%m-%Y | %I:%M %p')} IST</i>\n"
    msg += f"📈 <b>Market Trend:</b> {sentiment} ({green_count}/{len(results)} Green)\n"
    msg += f"───────────────────\n\n"
    
    for _, row in df.iterrows():
        # Add Trophy to the Day's Top Gainer
        prefix = "🏆 " if row['Symbol'] == top_gainer_symbol else ""
        
        msg += f"{prefix}<b>{row['Symbol']}</b>  ➔  🔵 <b>₹{row['LTP']}</b>\n"
        msg += f"<code>Range: {row['52W_Dist']} from 52W High</code>\n"
        
        # Grid Layout for Returns
        msg += f"<code>DAY   | 1W    | 1M    | 3M</code>\n"
        msg += f"<code>{row['Day'].ljust(5)} | {row['1W'].ljust(5)} | {row['1M'].ljust(5)} | {row['3M'].ljust(5)}</code>\n"
        msg += f"<code>6M    | 1Y</code>\n"
        msg += f"<code>{row['6M'].ljust(5)} | {row['1Y'].ljust(5)}</code>\n"
        msg += f"───────────────────\n"

    # 6. Send to Telegram
    TOKEN = os.getenv('BOT_TOKEN')
    raw_ids = os.getenv('TELEGRAM_CHAT_ID') 
    
    if TOKEN and raw_ids:
        # Supports multiple IDs (comma separated)
        chat_ids = [id.strip() for id in raw_ids.split(',')]
        for chat_id in chat_ids:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id, 
                "text": msg, 
                "parse_mode": "HTML"
            }
            requests.post(url, data=payload)

if __name__ == "__main__":
    main()
