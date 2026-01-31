import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ================= CONFIG =================

TOKEN = "8371364402:AAGZ2cvg-ORwnKcnyjxeA-Npl_alW2GK8Tw"
API_KEY = "YPZLLME4OTH6V88M"

WARNING = "\n⚠️ البوت لغرض التعلم فقط والتداول تحت مسؤوليتك الشخصية"

BASE_URL = "https://www.alphavantage.co/query"

# ================= DATA =================

def get_price(symbol):
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }
    r = requests.get(BASE_URL, params=params).json()

    try:
        return float(r["Global Quote"]["05. price"])
    except:
        return None


def get_candles(symbol):
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "outputsize": "compact",
        "apikey": API_KEY
    }

    r = requests.get(BASE_URL, params=params).json()

    try:
        data = r["Time Series (5min)"]
        df = pd.DataFrame.from_dict(data, orient="index").astype(float)
        df = df.rename(columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. volume": "volume"
        })
        return df.sort_index()
    except:
        return None


# ================= ANALYSIS =================

def detect_trend(df):
    short = df["close"].rolling(10).mean()
    long = df["close"].rolling(30).mean()

    if short.iloc[-1] > long.iloc[-1]:
        return "صاعد 📈"
    elif short.iloc[-1] < long.iloc[-1]:
        return "هابط 📉"
    else:
        return "متذبذب ⚖️"


def support_resistance(df):
    support = round(df["low"].tail(40).min(), 2)
    resistance = round(df["high"].tail(40).max(), 2)
    return support, resistance


# ================= MAIN =================

def analyze(symbol):

    price = get_price(symbol)

    if not price:
        return "❌ لم يتم جلب السعر حالياً"

    df = get_candles(symbol)

    if df is None or len(df) < 30:
        return "❌ لم يتم جلب البيانات الفنية حالياً"

    trend = detect_trend(df)
    support, resistance = support_resistance(df)

    text = f"""
📌 الرمز: {symbol}
💵 السعر الحالي: {round(price,2)}

📉 الدعم: {support}
📈 المقاومة: {resistance}

━━━━━━━━━━

📊 الاتجاه: {trend}

{WARNING}
"""

    return text


# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في Radar Market الأسطوري\n"
        "أرسل رمز السهم مثل:\n"
        "TSLA\nAAPL\nSPX\nNDX"
        + WARNING
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    result = analyze(symbol)
    await update.message.reply_text(result)


# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING...")

app.run_polling()
