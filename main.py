import requests
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE = "https://api.twelvedata.com/time_series"

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


# ================= DATA =================

def get_data(symbol):
    params = {
        "symbol": symbol,
        "interval": "5min",
        "apikey": API_KEY,
        "outputsize": 200
    }

    r = requests.get(BASE, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df


# ================= INDICATORS =================

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


# ================= ANALYSIS =================

def analyze(df):
    close = df["close"]

    ema20 = ema(close, 20).iloc[-1]
    ema50 = ema(close, 50).iloc[-1]

    rsi_val = rsi(close).iloc[-1]

    price = close.iloc[-1]

    trend = "صاعد 📈" if ema20 > ema50 else "هابط 📉"

    support = close.tail(50).min()
    resistance = close.tail(50).max()

    momentum = "قوي 🚀" if rsi_val > 60 else "ضعيف ⚠️" if rsi_val < 40 else "متوازن ⚖️"

    target1 = price + (resistance - support) * 0.3
    target2 = price + (resistance - support) * 0.6

    stop = support

    text = f"""
📊 تحليل احترافي

السعر الحالي: {price:.2f}
الاتجاه: {trend}
الزخم: {momentum}

🧱 دعم: {support:.2f}
🚧 مقاومة: {resistance:.2f}

🎯 أهداف مضاربية:
1️⃣ {target1:.2f}
2️⃣ {target2:.2f}

⛔ وقف الخسارة: {stop:.2f}
"""

    return text


# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def analyze_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()

    df = get_data(symbol)

    if df is None:
        await update.message.reply_text("❌ الرمز غير صحيح أو لا توجد بيانات حالياً")
        return

    result = analyze(df)

    await update.message.reply_text(result)


# ================= RUN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_symbol))

    print("Radar Market Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()