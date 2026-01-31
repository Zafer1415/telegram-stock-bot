import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ================= CONFIG =================

TOKEN = "8371364402:AAGZ2cvg-ORwnKcnyjxeA-Npl_alW2GK8Tw"
API_KEY = "d5ujrrpr01qr4f89gi70d5ujrrpr01qr4f89gi7g"

WARNING = "\n⚠️ البوت لغرض التعلم فقط والتداول تحت مسؤوليتك الشخصية"

# ================= DATA =================

def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
    r = requests.get(url).json()
    return r.get("c")

def get_candles(symbol, resolution):
    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "count": 200,
        "token": API_KEY
    }
    r = requests.get(url, params=params).json()
    if r.get("s") != "ok":
        return None
    return pd.DataFrame({
        "close": r["c"],
        "high": r["h"],
        "low": r["l"],
        "volume": r["v"]
    })

# ================= ANALYSIS BASE =================

def detect_trend(df):
    short = df["close"].rolling(20).mean()
    long = df["close"].rolling(50).mean()

    if short.iloc[-1] > long.iloc[-1]:
        return "صاعد 📈"
    elif short.iloc[-1] < long.iloc[-1]:
        return "هابط 📉"
    else:
        return "متذبذب ⚖️"

def support_resistance(df):
    support = round(df["low"].tail(40).min(),2)
    resistance = round(df["high"].tail(40).max(),2)
    return support, resistance

# ================= MAIN ANALYSIS =================

def analyze(symbol):

    price = get_price(symbol)
    if not price:
        return "❌ الرمز غير مدعوم أو مشكلة في API"

    df_fast = get_candles(symbol,"5")   # سكالبينج
    df_day = get_candles(symbol,"60")   # يومي
    df_week = get_candles(symbol,"D")   # سوينغ

    if df_fast is None:
        return "❌ لم يتم جلب البيانات"

    trend_fast = detect_trend(df_fast)
    trend_general = detect_trend(df_week)

    support_day, resistance_day = support_resistance(df_day)
    support_week, resistance_week = support_resistance(df_week)

    market_state = "ترند" if trend_fast == trend_general else "متذبذب"

    text = f"""
📌 السهم/المؤشر: {symbol}
💵 السعر الحالي: {round(price,2)}

📍 الدعم اليومي: {support_day}
📍 المقاومة اليومية: {resistance_day}

📍 الدعم الأسبوعي: {support_week}
📍 المقاومة الأسبوعية: {resistance_week}

━━━━━━━━━━━━━━

📈 الاتجاه العام: {trend_general}
⚡ الاتجاه اللحظي: {trend_fast}
📊 حالة السوق: {market_state}

{WARNING}
"""

    return text

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في Radar Market الأسطوري\n"
        "أرسل رمز السهم أو المؤشر مثل:\n"
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
