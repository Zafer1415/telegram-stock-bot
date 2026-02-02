
import requests
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE = "https://api.twelvedata.com/time_series"

WELCOME = """أهلاً بك في 👋
🤖 Radar Market 🤖

أرسل رمز السهم أو المؤشر مثل:
TSLA
AAPL
META
SPX
NDX

⚠️ البوت لا يقدم أي استشارات مالية إطلاقاً  
لغرض التعلم فقط ✋🏻
"""

# ================= DATA =================

def get_df(symbol, interval="5min"):
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": 300,
        "include_prepost": "true"
    }

    r = requests.get(BASE, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"]).astype(float)
    return df.iloc[::-1]

# ================= INDICATORS =================

def ema(s, n):
    return s.ewm(span=n).mean()

def rsi(s, p=14):
    d = s.diff()
    gain = d.clip(lower=0).rolling(p).mean()
    loss = -d.clip(upper=0).rolling(p).mean()
    rs = gain / loss
    return 100 - (100/(1+rs))

def liquidity_zones(series):
    high_zone = series.tail(50).max()
    low_zone = series.tail(50).min()
    return low_zone, high_zone

def fibonacci(high, low):
    diff = high - low
    return {
        "23%": high - diff*0.236,
        "38%": high - diff*0.382,
        "50%": high - diff*0.5,
        "61%": high - diff*0.618
    }

# ================= ANALYSIS =================

def analyze(df):

    close = df["close"]

    ema20 = ema(close,20)
    ema50 = ema(close,50)
    ema200 = ema(close,200)

    rsi_val = rsi(close).iloc[-1]
    price = close.iloc[-1]

    trend = "صاعد قوي 🚀" if ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1] else \
            "هابط قوي 🔻" if ema20.iloc[-1] < ema50.iloc[-1] < ema200.iloc[-1] else \
            "تذبذب ⚖️"

    momentum = "زخم ناري 🔥" if rsi_val > 65 else "ضغط بيعي ⚠️" if rsi_val < 35 else "متوازن"

    support, resistance = liquidity_zones(close)

    fib = fibonacci(resistance, support)

    target_scalp = resistance
    target_extended = resistance + (resistance-support)*1.2

    stop = support - (resistance-support)*0.25

    return {
        "price":round(price,2),
        "trend":trend,
        "momentum":momentum,
        "rsi":round(rsi_val,1),
        "support":round(support,2),
        "resistance":round(resistance,2),
        "fib": {k:round(v,2) for k,v in fib.items()},
        "target1":round(target_scalp,2),
        "target2":round(target_extended,2),
        "stop":round(stop,2)
    }

# ================= TELEGRAM =================

def fix_symbol(sym):
    sym=sym.upper().strip()
    if sym=="SPX": return "SPX:IND"
    if sym=="NDX": return "NDX:IND"
    return sym

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def handle_symbol(update:Update, context:ContextTypes.DEFAULT_TYPE):

    symbol = fix_symbol(update.message.text)

    try:
        df = get_df(symbol)
        if df is None:
            await update.message.reply_text("❌ لا توجد بيانات حالياً")
            return

        r = analyze(df)

        msg=f"""
📊 تحليل أسطوري لـ {symbol}

السعر: {r["price"]}

📈 الإتجاه: {r["trend"]}
⚡ الزخم: {r["momentum"]}
RSI: {r["rsi"]}

💧 منطقة سيولة سفلى: {r["support"]}
💧 منطقة سيولة عليا: {r["resistance"]}

📐 فيبوناتشي:
23% ➝ {r["fib"]["23%"]}
38% ➝ {r["fib"]["38%"]}
50% ➝ {r["fib"]["50%"]}
61% ➝ {r["fib"]["61%"]}

🎯 هدف مضاربي: {r["target1"]}
🚀 هدف ممتد: {r["target2"]}

🛑 وقف خسارة ذكي: {r["stop"]}

⚠️ التزم بإدارة المخاطر
"""

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("⚠️ النظام يحدّث حالياً")

# ================= RUN =================

def main():
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_symbol))
    app.run_polling()

if __name__=="__main__":
    main()