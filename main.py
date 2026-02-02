import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE_URL = "https://api.twelvedata.com/time_series"

WELCOME_MSG = """👋 أهلاً بك في 🤖 Radar Market 🤖

أرسل رمز السهم أو المؤشر مثل:
TSLA
AAPL
META
SPX
NDX

⚠️ البوت لا يقدم أي استشارات مالية أو توصيات تداول إطلاقاً  
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

    r = requests.get(BASE_URL, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df


# ================= ANALYSIS =================

def analyze(df):
    close = df["close"]

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    trend = "صاعد 📈" if ema20.iloc[-1] > ema50.iloc[-1] else "هابط 📉"

    high = df["high"].max()
    low = df["low"].min()

    price = close.iloc[-1]

    target1 = price * 1.01
    target2 = price * 1.03

    stop = price * 0.98

    return {
        "trend": trend,
        "price": round(price, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "t1": round(target1, 2),
        "t2": round(target2, 2),
        "stop": round(stop, 2)
    }


# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG)


async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()

    df = get_data(symbol)

    if df is None:
        await update.message.reply_text("❌ لم يتم العثور على بيانات لهذا الرمز")
        return

    a = analyze(df)

    msg = f"""
📊 تحليل {symbol}

السعر الحالي: {a['price']}
الاتجاه: {a['trend']}

📍 أعلى منطقة: {a['high']}
📍 أدنى منطقة: {a['low']}

🎯 هدف مضارب: {a['t1']}
🎯 هدف ممتد: {a['t2']}

🛑 وقف خسارة: {a['stop']}

⚠️ التزم بإدارة رأس المال
"""

    await update.message.reply_text(msg)


# ================= RUN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()