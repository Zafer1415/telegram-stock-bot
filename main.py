import requests
import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== CONFIG ==================

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE_URL = "https://api.twelvedata.com/time_series"

WARNING = "⚠️ البوت للتعلم فقط ولا يقدم أي توصيات مالية"

# ================== DATA ==================

def get_data(symbol, interval="5min"):
    params = {
        "symbol": symbol,
        "interval": interval,
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


# ================== ANALYSIS ==================

def analyze(df):
    close = df["close"]

    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    price = close.iloc[-1]

    trend = "📈 صاعد قوي" if ema20 > ema50 else "📉 هابط قوي"

    support = df["low"].rolling(20).min().iloc[-1]
    resistance = df["high"].rolling(20).max().iloc[-1]

    target1 = resistance
    target2 = resistance + (resistance - support)

    stop = support

    msg = f"""
📊 تحليل احترافي

السعر الحالي: {price:.2f}

الإتجاه: {trend}

🟢 دعم قوي: {support:.2f}
🔴 مقاومة قوية: {resistance:.2f}

🎯 هدف لحظي: {target1:.2f}
🎯 هدف ممتد: {target2:.2f}

🛑 وقف خسارة: {stop:.2f}

{WARNING}
"""

    return msg


# ================== BOT ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"""👋 أهلاً بك في 🤖 Radar Market 🤖

أرسل رمز السهم أو المؤشر مثل:
TSLA
AAPL
META
SPX
NDX

⚠️ البوت لا يقدم أي استشارات مالية إطلاقاً
لغرض التعلم فقط ✋🏻
"""
    )


async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()

    df = get_data(symbol)

    if df is None:
        await update.message.reply_text("❌ لم أستطع جلب البيانات حالياً")
        return

    analysis = analyze(df)
    await update.message.reply_text(analysis)


# ================== RUN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()