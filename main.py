import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================

TOKEN = "8371364402:AAGZ2cvg-ORwnKcnyjxeA-Npl_alW2GK8Tw"
API_KEY = "MJOLKI1JQV4E7PJX"

BASE_URL = "https://www.alphavantage.co/query"

WARNING = "\n⚠️ للتحليل الفني فقط والتداول تحت مسؤوليتك الشخصية"

# ================== DATA ==================

def get_price(symbol):
    url = f"{BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    data = requests.get(url).json()
    try:
        return float(data["Global Quote"]["05. price"])
    except:
        return None

def get_rsi(symbol):
    url = f"{BASE_URL}?function=RSI&symbol={symbol}&interval=5min&time_period=14&series_type=close&apikey={API_KEY}"
    data = requests.get(url).json()
    try:
        last = list(data["Technical Analysis: RSI"].values())[0]
        return float(last["RSI"])
    except:
        return None

# ================== ANALYSIS ==================

def analyze(symbol):
    price = get_price(symbol)
    rsi = get_rsi(symbol)

    if not price or not rsi:
        return "❌ لم يتم جلب البيانات حالياً (انتظر دقيقة وجرب مرة أخرى)"

    if rsi > 60:
        signal = "🚀 شراء قوي"
        trend = "📈 صاعد قوي"
    elif rsi < 40:
        signal = "🛑 بيع قوي"
        trend = "📉 هابط قوي"
    else:
        signal = "⏸ انتظار"
        trend = "➡️ تذبذب"

    scalp_target = round(price * 1.01, 2)
    swing_target = round(price * 1.05, 2)
    drop_target = round(price * 0.97, 2)

    message = f"""
📊 تحليل فني احترافي لـ {symbol}

💲 السعر الحالي: {price}

📈 الاتجاه العام: {trend}
📉 RSI: {round(rsi,2)}

🎯 الإشارة:
{signal}

⚡ أهداف سريعة:
➡️ {scalp_target}

🎯 أهداف ممتدة:
➡️ {swing_target}

📉 في حال كسر السعر:
⬇️ {drop_target}

{WARNING}
"""

    return message

# ================== TELEGRAM ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في Radar Market الأسطوري\n\nأرسل رمز السهم مثل:\nTSLA\nAAPL\nSPX\nNDX"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    result = analyze(symbol)
    await update.message.reply_text(result)

# ================== RUN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
