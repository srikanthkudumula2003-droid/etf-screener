import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime
import pytz

# 1. SETUP - UPDATED LIST
# Removed MON100, Added AUTOBEES
SYMBOLS = ['MASPTOP50.NS', 'ITBEES.NS', 'BANKIETF.NS', 'PHARMABEES.NS', 'MAHKTECH.NS', 'AUTOBEES.NS', 'GROWWEV.NS']
IST = pytz.timezone('Asia/Kolkata')

def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='2y')
        if len(df) < 252: return None
        
        ltp = df['Close'].iloc[-1]
        day_chg = ((ltp - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        high_52w = df['High'].tail(252).max()
        dist_52w = ((ltp - high_52w) / high_52w) * 100

        def pct_with_icon(days):
            old = df['Close'].iloc[-days]
            val = ((ltp - old) / old) * 100
            icon = "🟢" if val >= 0 else "🔴"
            return f"{icon}{val:+.1f}%"

        return {
            'Symbol': symbol.replace('.NS', ''),
            'Full_Ticker': symbol,
            'LTP': f"{ltp:.2f}",
            'Day': f"{'🟢' if day_chg >= 0 else '🔴'}{day_chg:+.1f}%",
            '52W_Dist': f"{dist_52w:.1f}%",
            '1W': pct_with_icon(5), '1M': pct_with_icon(21), 
            '3M': pct_with_icon(63), '6M': pct_with_icon(126), 
            '1Y': pct_with_icon(252), 'Raw_Chg': day_chg
        }
    except: return None

def main():
    results = [get_data(s) for s in SYMBOLS if get_data(s)]
    results.sort(key=lambda x: x['Raw_Chg'], reverse=True)
    
    ist_now = datetime.now(IST)
    green_count = sum(1 for r in results if "🟢" in r['Day'])
    sentiment = "BULLISH 📈" if green_count > len(results)/2 else "BEARISH 📉"

    msg = f"📊 <b>ETF PERFORMANCE INSIGHTS</b>\n"
    msg += f"📅 <b>Date:</b> {ist_now.strftime('%d-%m-%Y')}\n"
    msg += f"⏰ <b>Time:</b> {ist_now.strftime('%I:%M %p')} IST\n"
    msg += f"📊 <b>Market Trend:</b> {sentiment} ({green_count}/{len(results)} Green)\n"
    msg += f"───────────────────\n\n"

    for i, row in enumerate(results):
        prefix = "🏆 " if i == 0 else "🔹 "
        yf_link = f"https://finance.yahoo.com/quote/{row['Full_Ticker']}"
        msg += f"{prefix}<a href='{yf_link}'><b>{row['Symbol']}</b></a> ➔ LTP: 🔵 <b>₹{row['LTP']}</b>\n"
        msg += f"<code>Range: {row['52W_Dist']} from 52W High</code>\n"
        msg += f"<code>DAY      | 1W       | 1M</code>\n"
        msg += f"<code>{row['Day'].ljust(8)} | {row['1W'].ljust(8)} | {row['1M'].ljust(8)}</code>\n"
        msg += f"<code>3M       | 6M       | 1Y</code>\n"
        msg += f"<code>{row['3M'].ljust(8)} | {row['6M'].ljust(8)} | {row['1Y'].ljust(8)}</code>\n"
        msg += f"───────────────────\n"

    msg += f"\n⚠️ <b>Note:</b> These updates are for educational purpose and based on NSE data. Always consult a financial advisor before investing."

    token = os.getenv('BOT_TOKEN')
    chat_ids = os.getenv('TELEGRAM_CHAT_ID', '').split(',')
    for cid in chat_ids:
        payload = {
            "chat_id": cid.strip(), 
            "text": msg, 
            "parse_mode": "HTML",
            "disable_web_page_preview": True 
        }
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=payload)

if __name__ == "__main__":
    main()
