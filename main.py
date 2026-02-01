import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "70f12cfac5e34ee3bc35f124ec37d547"

WARNING = "\n⚠️ البوت لغرض التعلم فقط والتداول تحت مسؤوليتك الشخصية"

BASE = "https://api.twelvedata.com/time_series"

# ================= DATA =================

def get_df(symbol, interval):
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

# ================= INDICATORS =================

def ema(series, n):
    return series.ewm(span=n).mean()

def trend(df):
    e50 = ema(df["close"], 50)
    e200 = ema(df["close"], 200)

    if e50.iloc[-1] > e200.iloc[-1]:
        return "صاعد 📈"
    elif e50.iloc[-1] < e200.iloc[-1]:
        return "هابط 📉"
    else:
        return "متذبذب ⚖️"

def support_resistance(df):
    support = round(df["low"].tail(40).min(),2)
    resistance = round(df["high"].tail(40).max(),2)
    return support, resistance

# ================= ANALYSIS =================

def analyze(symbol):

    df_fast = get_df(symbol,"5min")
    df_day = get_df(symbol,"1h")
    df_week = get_df(symbol,"1day")

    if df_fast is None:
        return "❌ لم يتم جلب البيانات (تحقق من الرمز)"

    price = round(df_fast["close"].iloc[-1],2)

    trend_fast = trend(df_fast)
    trend_general = trend(df_week)

    sup_day, res_day = support_resistance(df_day)
    sup_week, res_week = support_resistance(df_week)

    market_state = "ترند" if trend_fast == trend_general else "متذبذب"

    # أهداف ذكية حسب الاتجاه
    if "صاعد" in trend_general:
        targets = [
            res_day,
            round(res_day + (res_day-sup_day)*0.5,2),
            round(res_day + (res_day-sup_day),2)
        ]
        stop = sup_day
        target_text = f"""
🎯 أهداف الصعود:
• {targets[0]}
• {targets[1]}
• {targets[2]}
🛑 وقف الخسارة: {stop}
"""
    elif "هابط" in trend_general:
        targets = [
            sup_day,
            round(sup_day - (res_day-sup_day)*0.5,2),
            round(sup_day - (res_day-sup_day),2)
        ]
        stop = res_day
        target_text = f"""
🎯 أهداف الهبوط:
• {targets[0]}
• {targets[1]}
• {targets[2]}
🛑 وقف الخسارة: {stop}
"""
    else:
        target_text = "⚠️ السوق متذبذب — يفضل الانتظار"

    text = f"""
📌 الرمز: {symbol}
💵 السعر الحالي: {price}

📍 الدعم اليومي: {sup_day}
📍 المقاومة اليومية: {res_day}

📍 الدعم الأسبوعي: {sup_week}
📍 المقاومة الأسبوعية: {res_week}

━━━━━━━━━━━━━━

📈 الاتجاه العام: {trend_general}
⚡ الاتجاه اللحظي: {trend_fast}
📊 حالة السوق: {market_state}

{target_text}
{WARNING}
"""

    return text

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في Radar Market المؤسسي\n"
        "أرسل رمز أي سهم أو مؤشر مثل:\n"
        "TSLA\nAAPL\nSPX\nNDX"
        + WARNING
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    try:
        result = analyze(symbol)
        await update.message.reply_text(result)
    except:
        await update.message.reply_text("❌ خطأ في التحليل")

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("✅ BOT RUNNING ...")
app.run_polling()
