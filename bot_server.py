import asyncio
import logging
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعدادات البوت
TOKEN = "7618310902:AAFXPN4Vx0nJRbPXeCEiAQXfvjnV-OQYC20"
AUTHORIZED_CHAT_ID = None
PENDING_REQUESTS = {}

# إعدادات اللوج
logging.basicConfig(level=logging.INFO)

# إنشاء تطبيق Flask
app = Flask(__name__)
bot_app: Application = None

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED_CHAT_ID
    AUTHORIZED_CHAT_ID = update.effective_chat.id
    await update.message.reply_text("✅ تم تسجيل هذا الحساب لتلقي إشعارات التشغيل.")

# تنفيذ القرار
async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ip, decision = query.data.split(":")
    PENDING_REQUESTS[ip] = decision
    await query.edit_message_text(f"📥 تم اختيار: {decision.upper()} لتشغيل الجهاز {ip}")

# إرسال إشعار
async def send_telegram_alert(ip):
    keyboard = [
        [InlineKeyboardButton("✅ سماح", callback_data=f"{ip}:allowed"),
         InlineKeyboardButton("❌ رفض", callback_data=f"{ip}:denied")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    try:
        await bot_app.bot.send_message(
            chat_id=AUTHORIZED_CHAT_ID,
            text=f"⚠️ محاولة تشغيل جديدة من الجهاز IP: {ip}\nهل تسمح بالتشغيل؟",
            reply_markup=markup
        )
    except Exception as e:
        print(f"❌ فشل في إرسال الرسالة: {e}")

# API: طلب السماح
@app.route("/request", methods=["POST"])
def request_access():
    data = request.get_json()
    ip = data.get("ip")
    print(f"🚀 إرسال طلب تشغيل إلى البوت للسماح لـ IP: {ip}")
    PENDING_REQUESTS[ip] = None
    asyncio.run(send_telegram_alert(ip))
    return jsonify({"status": "pending"})

# API: فحص الرد
@app.route("/check/<ip>", methods=["GET"])
def check_status(ip):
    return jsonify({"status": PENDING_REQUESTS.get(ip, "pending")})

# Flask في Thread منفصل
def run_flask():
    print("🌐 Flask API Started...")
    app.run(host="0.0.0.0", port=8000)

# Main async
async def main():
    global bot_app
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(handle_decision))

    print("✅ Telegram Bot Started...")
    Thread(target=run_flask, daemon=True).start()
    await bot_app.run_polling(close_loop=False)

# تشغيل
if __name__ == "__main__":
    asyncio.run(main())
