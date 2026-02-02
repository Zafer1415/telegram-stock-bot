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

⚠️ البوت لا يقدم أي استشارات مالية أو توصيات تداول إطلاقاً  
وضع لغرض التعلم فقط ✋🏻
"""

# ================== DATA ==================

def fetch(symbol, interval="5min"):
    params = {
        "symbol": symbol,
        "interval": interval,
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


# ================== INDICATORS ==================

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

def liquidity_zones(df):
    high_zone = df["high"].rolling(20).max().iloc[-1]
    low_zone = df["low"].rolling(20).min().iloc[-1]
    return high_zone, low_zone


# ================== ANALYSIS ==================

def analyze(symbol):
    df = fetch(symbol)

    if df is None or len(df) < 50:
        return "⚠️ البيانات غير متوفرة حالياً حاول بعد قليل"

    close = df["close"]

    ema50 = ema(close, 50).iloc[-1]
    ema200 = ema(close, 200).iloc[-1]
    rsi_val = rsi(close).iloc[-1]

    price = close.iloc[-1]

    high_liq, low_liq = liquidity_zones(df)

    trend = "📈 صاعد" if ema50 > ema200 else "📉 هابط"

    momentum = "قوي" if rsi_val > 60 else "ضعيف" if rsi_val < 40 else "متوازن"

    target_near = price * 1.01 if trend == "📈 صاعد" else price * 0.99
    target_far = price * 1.03 if trend == "📈 صاعد" else price * 0.97
    stop = price * 0.985 if trend == "📈 صاعد" else price * 1.015

    msg = f"""
📊 تحليل احترافي لـ {symbol}

💰 السعر الحالي: {price:.2f}
📈 الاتجاه العام: {trend}
⚡ الزخم: {momentum}
📉 RSI: {rsi_val:.2f}

💧 مناطق السيولة:
🔼 سيولة عليا: {high_liq:.2f}
🔽 سيولة سفلى: {low_liq:.2f}

🎯 أهداف مضاربية:
➡️ هدف قريب: {target_near:.2f}
➡️ هدف ممتد: {target_far:.2f}

🛑 وقف خسارة ذكي:
{stop:.2f}

⚠️ التزم بإدارة رأس المال دائماً
"""

    return msg


# ================== TELEGRAM ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()

    await update.message.reply_text("⏳ جاري التحليل الاحترافي...")

    try:
        result = analyze(symbol)
    except Exception as e:
        result = "⚠️ حصل خطأ أثناء التحليل حاول لاحقاً"

    await update.message.reply_text(result)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()