import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================

TOKEN = "8371364402:AAGeGPnHgJeF4tzu-N4e9wz57KS0mnyi2V0"
API_KEY = "499390a50ae1446e849a83e418c1857f"

BASE = "https://api.twelvedata.com/time_series"

WELCOME = """أهلاً بك في 👋
🤖 Radar Market 🤖

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

def get_df(symbol, interval="5min"):

    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": 200,
        "include_prepost": "true"
    }

    r = requests.get(BASE, params=params).json()

    if "values" not in r or len(r["values"]) == 0:
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
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze(df):

    close = df["close"]

    ema20 = ema(close, 20)
    ema50 = ema(close, 50)

    rsi_val = rsi(close).iloc[-1]

    price = close.iloc[-1]

    trend = "صاعد 📈" if ema20.iloc[-1] > ema50.iloc[-1] else "هابط 📉"

    momentum = "قوي 🔥" if rsi_val > 60 else "ضعيف ⚠️" if rsi_val < 40 else "متوازن ⚖️"

    support = close.tail(20).min()
    resistance = close.tail(20).max()

    target_near = resistance
    target_far = resistance + (resistance - support)

    return {
        "price": round(price,2),
        "trend": trend,
        "momentum": momentum,
        "support": round(support,2),
        "resistance": round(resistance,2),
        "target1": round(target_near,2),
        "target2": round(target_far,2),
        "rsi": round(rsi_val,1)
    }

# ================== TELEGRAM ==================

def fix_symbol(sym):
    sym = sym.upper().strip()

    if sym == "SPX":
        return "SPX:IND"
    if sym == "NDX":
        return "NDX:IND"

    return sym

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):

    symbol = fix_symbol(update.message.text)

    try:
        df = get_df(symbol)

        if df is None:
            await update.message.reply_text("❌ لا توجد بيانات حالياً لهذا الرمز")
            return

        result = analyze(df)

        msg = f"""
📊 تحليل {symbol}

السعر الحالي: {result["price"]}

الإتجاه: {result["trend"]}
الزخم: {result["momentum"]}
RSI: {result["rsi"]}

🟢 دعم: {result["support"]}
🔴 مقاومة: {result["resistance"]}

🎯 هدف مضاربي: {result["target1"]}
🚀 هدف ممتد: {result["target2"]}

⚠️ الالتزام بوقف الخسارة ضروري
"""

        await update.message.reply_text(msg)

    except Exception as e:
        print(e)
        await update.message.reply_text("⚠️ خطأ في النظام جاري التحديث وشكراً 🙏")

# ================== RUN ==================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    print("Radar Market Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()