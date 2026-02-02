import requests
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================

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

# ================== DATA ==================

def get_data(symbol, interval="5min"):
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": 300
    }

    r = requests.get(BASE_URL, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df


# ================== INDICATORS ==================

def ema(series, n):
    return series.ewm(span=n).mean()

def rsi(series, n=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(n).mean()
    avg_loss = loss.rolling(n).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def analyze(df):

    close = df["close"]

    ema20 = ema(close,20)
    ema50 = ema(close,50)

    rsi_val = rsi(close).iloc[-1]

    price = close.iloc[-1]

    trend = "📉 هابط" if ema20.iloc[-1] < ema50.iloc[-1] else "📈 صاعد"

    support = close.tail(50).min()
    resistance = close.tail(50).max()

    liquidity_low = support * 0.995
    liquidity_high = resistance * 1.005

    target_short = price + (resistance-price)*0.5
    target_long = resistance

    stop_loss = support

    return {
        "price": price,
        "trend": trend,
        "rsi": round(rsi_val,1),
        "support": round(support,2),
        "resistance": round(resistance,2),
        "liq_low": round(liquidity_low,2),
        "liq_high": round(liquidity_high,2),
        "target1": round(target_short,2),
        "target2": round(target_long,2),
        "stop": round(stop_loss,2)
    }


# ================== BOT ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):

    symbol = update.message.text.strip().upper()

    await update.message.reply_text("⏳ جاري التحليل العميق...")

    df = get_data(symbol)

    if df is None:
        await update.message.reply_text("❌ لم يتم العثور على الرمز")
        return

    a = analyze(df)

    msg = f"""
📊 تحليل {symbol}

💰 السعر الحالي: {a['price']}

📈 الاتجاه: {a['trend']}
📉 RSI: {a['rsi']}

🟢 دعم قوي: {a['support']}
🔴 مقاومة قوية: {a['resistance']}

💧 مناطق السيولة:
⬇️ {a['liq_low']}
⬆️ {a['liq_high']}

🎯 أهداف مضاربة:
هدف لحظي: {a['target1']}
هدف ممتد: {a['target2']}

🛑 وقف خسارة: {a['stop']}

⚠️ التزم بالإدارة المالية
"""

    await update.message.reply_text(msg)


# ================== RUN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Radar Market Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()