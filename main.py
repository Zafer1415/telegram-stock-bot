import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================

TOKEN = "8371364402:AAGZ2cvg-ORwnKcnyjxeA-Npl_alW2GK8Tw"
FINNHUB_KEY = "d5ujrrpr01qr4f89gi70d5ujrrpr01qr4f89gi7g"

WARNING = "\n\n⚠️ البوت للتعلم فقط والتداول على مسؤوليتك الشخصية"

# ================= DATA =================

def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    r = requests.get(url).json()
    return r.get("c")

def get_candles(symbol, resolution):
    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "count": 200,
        "token": FINNHUB_KEY
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

def get_sector(symbol):
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_KEY}"
    r = requests.get(url).json()
    return r.get("finnhubIndustry", "غير معروف")

# ================= ANALYSIS =================

def trend(df):
    ema20 = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    ema50 = ta.trend.EMAIndicator(df["close"], 50).ema_indicator()

    if ema20.iloc[-1] > ema50.iloc[-1]:
        return "صاعد 📈"
    elif ema20.iloc[-1] < ema50.iloc[-1]:
        return "هابط 📉"
    else:
        return "متذبذب ⚖️"

def support_resistance(df):
    support = round(df["low"].tail(30).min(), 2)
    resistance = round(df["high"].tail(30).max(), 2)
    return support, resistance

def liquidity(df):
    avg = df["volume"].mean()
    last = df["volume"].iloc[-1]

    if last > avg * 1.5:
        return "عالية 💧"
    elif last < avg * 0.7:
        return "ضعيفة ❄️"
    else:
        return "طبيعية ⚖️"

def build_targets(direction, support, resistance):

    diff = resistance - support

    if direction == "صاعد 📈":
        targets = [
            resistance,
            round(resistance + diff * 0.5, 2),
            round(resistance + diff, 2)
        ]
        return targets, None, support

    if direction == "هابط 📉":
        targets = [
            support,
            round(support - diff * 0.5, 2),
            round(support - diff, 2)
        ]
        return None, targets, resistance

    return None, None, None

# ================= MAIN =================

def analyze(symbol):

    price = get_price(symbol)
    if not price:
        return "❌ لم يتم جلب السعر"

    df_day = get_candles(symbol, "60")
    df_week = get_candles(symbol, "D")
    df_fast = get_candles(symbol, "5")

    if df_day is None or df_week is None or df_fast is None:
        return "❌ مشكلة في البيانات"

    trend_general = trend(df_week)
    trend_live = trend(df_fast)

    support_day, resistance_day = support_resistance(df_day)
    support_week, resistance_week = support_resistance(df_week)

    liq = liquidity(df_fast)
    sector = get_sector(symbol)

    up_targets, down_targets, stop = build_targets(
        trend_general,
        support_day,
        resistance_day
    )

    market_state = "ترند" if trend_general == trend_live else "متذبذب"

    text = f"""
🏭 القطاع: {sector}
📌 الرمز: {symbol}
💵 السعر الحالي: {round(price,2)}

📍 الدعم اليومي: {support_day}
📍 المقاومة اليومية: {resistance_day}

📍 الدعم الأسبوعي: {support_week}
📍 المقاومة الأسبوعية: {resistance_week}

━━━━━━━━━━━━━━

📈 الاتجاه العام: {trend_general}
⚡ الاتجاه اللحظي: {trend_live}
📊 حالة السوق: {market_state}
💧 السيولة: {liq}

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
        "👋 أهلاً بك في بوت تحليل الأسهم\n"
        "أرسل رمز السهم مثل:\nTSLA\nAAPL\nSPX"
        + WARNING
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    try:
        result = analyze(symbol)
        await update.message.reply_text(result)
    except:
        await update.message.reply_text("❌ حدث خطأ أثناء التحليل")

# ================= RUN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("✅ BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
