import requests
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE_URL = "https://api.twelvedata.com/time_series"

WELCOME = """👋 أهلاً بك في 🤖 Radar Market 🤖

أرسل رمز السهم أو المؤشر مثل:
TSLA
AAPL
META
SPX
NDX

⚠️ البوت لا يقدم أي استشارات مالية إطلاقاً
وضع لغرض التعلم فقط ✋🏻
"""

# ===================== DATA =====================

def get_data(symbol):
    params = {
        "symbol": symbol,
        "interval": "5min",
        "apikey": API_KEY,
        "outputsize": 200
    }

    r = requests.get(BASE_URL, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df

# ===================== INDICATORS =====================

def ema(series, n):
    return series.ewm(span=n).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze(df):
    close = df["close"]

    df["EMA20"] = ema(close, 20)
    df["EMA50"] = ema(close, 50)
    df["RSI"] = rsi(close)

    price = close.iloc[-1]

    trend = "صاعد 🚀" if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1] else "هابط 🔻"

    momentum = "قوي 💥" if df["RSI"].iloc[-1] > 60 else "ضعيف ⚠️"

    support = close.tail(50).min()
    resistance = close.tail(50).max()

    target_fast = price + (price - support)
    target_long = price + (resistance - support)

    stop = support

    report = f"""
📊 تحليل احترافي فوري

💵 السعر الحالي: {price:.2f}
📈 الاتجاه: {trend}
⚡ الزخم: {momentum}

🟢 منطقة دعم: {support:.2f}
🔴 منطقة مقاومة: {resistance:.2f}

🎯 هدف مضاربي سريع: {target_fast:.2f}
🎯 هدف ممتد بالزخم: {target_long:.2f}

🛑 وقف الخسارة: {stop:.2f}

⚠️ الاكتفاء بهدف مع الالتزام بوقف الخسارة
"""

    return report

# ===================== TELEGRAM =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()

    await update.message.reply_text("⏳ جاري التحليل الاحترافي...")

    df = get_data(symbol)

    if df is None:
        await update.message.reply_text("❌ الرمز غير صحيح أو البيانات غير متوفرة")
        return

    result = analyze(df)

    await update.message.reply_text(result)

# ===================== RUN =====================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Radar Market Bot Running...")

    app.run_polling()

if __name__ == "__main__":
    main()