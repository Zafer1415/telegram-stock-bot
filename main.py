import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ================= CONFIG =================

TOKEN = "8371364402:AAGZ2cvg-ORwnKcnyjxeA-Npl_alW2GK8Tw"
API_KEY = "d5ujrrpr01qr4f89gi70d5ujrrpr01qr4f89gi7g"

WARNING = "\n⚠️ البوت لغرض التعلم فقط والتداول تحت مسؤوليتك الشخصية"

# ================= SYMBOL FIX =================

def fix_symbol(symbol):
    if symbol == "SPX":
        return "^GSPC"
    if symbol == "NDX":
        return "^NDX"
    return symbol

# ================= DATA =================

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        r = requests.get(url, timeout=10).json()
        return r["c"] if "c" in r and r["c"] != 0 else None
    except:
        return None

def get_candles(symbol, resolution):
    try:
        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "count": 300,
            "token": API_KEY
        }

        r = requests.get(url, params=params, timeout=10).json()

        if r.get("s") != "ok":
            return None

        return pd.DataFrame({
            "close": r["c"],
            "high": r["h"],
            "low": r["l"],
            "volume": r["v"]
        })
    except:
        return None

# ================= INDICATORS =================

def detect_trend(df):
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "صاعد 📈"
    elif ma20.iloc[-1] < ma50.iloc[-1]:
        return "هابط 📉"
    else:
        return "عرضي ⚖️"

def support_resistance(df):
    support = round(df["low"].tail(50).min(), 2)
    resistance = round(df["high"].tail(50).max(), 2)
    return support, resistance

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs.iloc[-1])),2)

def macd(df):
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()

    if macd_line.iloc[-1] > signal.iloc[-1]:
        return "إيجابي 🔥"
    else:
        return "سلبي ❄️"

# ================= MAIN ANALYSIS =================

def analyze(symbol):

    price = get_price(symbol)
    if price is None:
        return "❌ لم يتم جلب السعر (API أو الرمز)"

    df_fast = get_candles(symbol, "5")
    df_day = get_candles(symbol, "60")
    df_week = get_candles(symbol, "D")

    if df_fast is None or df_day is None or df_week is None:
        return "❌ لم يتم جلب البيانات الفنية"

    trend_fast = detect_trend(df_fast)
    trend_general = detect_trend(df_week)

    support_day, resistance_day = support_resistance(df_day)
    support_week, resistance_week = support_resistance(df_week)

    rsi_value = rsi(df_day)
    macd_state = macd(df_day)

    if rsi_value > 70:
        rsi_state = "تشبع شراء ⚠️"
    elif rsi_value < 30:
        rsi_state = "تشبع بيع ✅"
    else:
        rsi_state = "متوازن"

    market_state = "ترند قوي 🚀" if trend_fast == trend_general else "تذبذب ⚖️"

    text = f"""
📊 Radar Market الأسطوري

📌 الرمز: {symbol}
💵 السعر: {round(price,2)}

━━━━━━━━━━━━━━

📍 دعم يومي: {support_day}
📍 مقاومة يومية: {resistance_day}

📍 دعم أسبوعي: {support_week}
📍 مقاومة أسبوعية: {resistance_week}

━━━━━━━━━━━━━━

📈 الاتجاه العام: {trend_general}
⚡ الاتجاه اللحظي: {trend_fast}
📊 حالة السوق: {market_state}

━━━━━━━━━━━━━━

📉 RSI: {rsi_value} ({rsi_state})
📈 MACD: {macd_state}

{WARNING}
"""

    return text

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في Radar Market الأسطوري\n\n"
        "أرسل رمز السهم أو المؤشر مثل:\n"
        "TSLA\nAAPL\nSPX\nNDX"
        + WARNING
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = fix_symbol(update.message.text.upper().strip())
    result = analyze(symbol)
    await update.message.reply_text(result)

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING...")
app.run_polling()
