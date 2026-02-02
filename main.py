import requests
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG =================

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE_URL = "https://api.twelvedata.com"

WARNING = "\n⚠️ البوت لا يقدم أي استشارات مالية أو توصيات تداول إطلاقاً\nوضع لغرض التعلم فقط ✋🏻"

# ================= DATA =================

def get_price(symbol):
    r = requests.get(f"{BASE_URL}/price?symbol={symbol}&apikey={API_KEY}",timeout=10).json()
    return float(r["price"]) if "price" in r else None

def get_candles(symbol, interval):
    r = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": symbol,
            "interval": interval,
            "apikey": API_KEY,
            "outputsize": 200
        },
        timeout=10
    ).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df

# ================= INDICATORS =================

def ma(series,n):
    return series.rolling(n).mean()

def rsi(series,period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    return 100 - (100/(1+rs))

def support_resistance(df):
    return round(df["low"].tail(40).min(),2), round(df["high"].tail(40).max(),2)

def liquidity(df):
    avg = df["volume"].mean()
    last = df["volume"].iloc[-1]

    if last > avg*1.3:
        return "دخول سيولة 💧"
    elif last < avg*0.7:
        return "خروج سيولة ❄️"
    else:
        return "سيولة طبيعية ⚖️"

# ================= TREND =================

def trend(df):
    m20 = ma(df["close"],20)
    m50 = ma(df["close"],50)

    if m20.iloc[-1] > m50.iloc[-1]:
        return "شراء 📈"
    elif m20.iloc[-1] < m50.iloc[-1]:
        return "بيع 📉"
    else:
        return "انتظار ⚖️"

def saturation(df):
    r = rsi(df["close"]).iloc[-1]

    if r > 70:
        return "تشبع شرائي 🔴"
    elif r < 30:
        return "تشبع بيعي 🟢"
    else:
        return "طبيعي ⚪"

# ================= TARGETS =================

def build_targets(price, direction, support, resistance):
    rng = abs(resistance-support)

    if "شراء" in direction:
        up = [
            round(resistance,2),
            round(resistance + rng*0.5,2),
            round(resistance + rng,2)
        ]
        stop = round(price - rng*0.25,2)
        return up, [], stop

    if "بيع" in direction:
        down = [
            round(support,2),
            round(support - rng*0.5,2),
            round(support - rng,2)
        ]
        stop = round(price + rng*0.25,2)
        return [], down, stop

    return [], [], None

# ================= ANALYSIS =================

def analyze(symbol):

    price = get_price(symbol)
    if not price:
        return "❌ رمز السهم غير صحيح"

    df_fast = get_candles(symbol,"5min")
    df_day  = get_candles(symbol,"1h")
    df_week = get_candles(symbol,"1day")

    if df_fast is None or df_day is None or df_week is None:
        return "⚠️ خطأ في النظام جاري تحديث النظام وشكراً 🙏"

    support_day, resistance_day = support_resistance(df_day)
    support_week, resistance_week = support_resistance(df_week)

    trend_general = trend(df_week)
    trend_live = trend(df_fast)

    market_state = "ترند" if trend_general == trend_live else "متذبذب"

    liq = liquidity(df_fast)
    sat = saturation(df_fast)

    up_targets, down_targets, stop = build_targets(
        price,
        trend_general,
        support_day,
        resistance_day
    )

    text = f"""
🤖 Radar Market 🤖

💵 السعر الحالي: {round(price,2)}

━━━━━━━━━━━━━━

📍 دعم يومي: {support_day}
📍 مقاومة يومية: {resistance_day}

📍 دعم أسبوعي: {support_week}
📍 مقاومة أسبوعية: {resistance_week}

━━━━━━━━━━━━━━

📈 الاتجاه العام: {trend_general}
⚡ الاتجاه اللحظي: {trend_live}
📊 حالة السوق: {market_state}

💧 السيولة: {liq}
📊 التشبع: {sat}

━━━━━━━━━━━━━━
"""

    if up_targets:
        text += f"""
🎯 أهداف الصعود:
• {up_targets[0]}
• {up_targets[1]}
• {up_targets[2]}

🛑 وقف الخسارة:
• {stop}
"""

    if down_targets:
        text += f"""
🎯 أهداف الهبوط:
• {down_targets[0]}
• {down_targets[1]}
• {down_targets[2]}

🛑 وقف الخسارة:
• {stop}
"""

    return text + WARNING

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في 🤖 Radar Market 🤖\n\n"
        "أرسل رمز السهم أو المؤشر مثل:\n"
        "TSLA\nAAPL\nMETA\nSPX\nNDX\n\n"
        "⚠️ البوت لا يقدم أي استشارات مالية أو توصيات تداول إطلاقاً\n"
        "وضع لغرض التعلم فقط ✋🏻"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    try:
        await update.message.reply_text(analyze(symbol))
    except:
        await update.message.reply_text("⚠️ خطأ في النظام جاري تحديث النظام وشكراً 🙏")

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Radar Market Running...")

app.run_polling()