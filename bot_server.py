import asyncio
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعدادات البوت
TOKEN = "7618310902:AAFXPN4Vx0nJRbPXeCEiAQXfvjnV-OQYC20"
AUTHORIZED_CHAT_ID = None
PENDING_REQUESTS = {}

# إعداد اللوج
logging.basicConfig(level=logging.INFO)

# إنشاء تطبيق Flask و Telegram
app = Flask(__name__)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED_CHAT_ID
    AUTHORIZED_CHAT_ID = update.effective_chat.id
    await update.message.reply_text("✅ تم تسجيل هذا الحساب لتلقي إشعارات التشغيل.")

async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    ip, decision = data[0], data[1]
    PENDING_REQUESTS[ip] = decision
    await query.edit_message_text(f"📥 تم اختيار: {decision.upper()} لتشغيل الجهاز {ip}")

async def send_telegram_alert(ip):
    keyboard = [
        [InlineKeyboardButton("✅ سماح", callback_data=f"{ip}:allowed"),
         InlineKeyboardButton("❌ رفض", callback_data=f"{ip}:denied")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if AUTHORIZED_CHAT_ID:
        await app.bot_app.bot.send_message(
            chat_id=AUTHORIZED_CHAT_ID,
            text=f"⚠️ محاولة تشغيل جديدة من الجهاز IP: {ip}\nهل تسمح بالتشغيل؟",
            reply_markup=reply_markup
        )

# API: طلب الوصول
@app.route("/request", methods=["POST"])
def request_access():
    data = request.get_json()
    ip = data.get("ip")
    print(f"🚀 إرسال طلب تشغيل إلى البوت للسماح لـ IP: {ip}")
    PENDING_REQUESTS[ip] = None
    asyncio.run_coroutine_threadsafe(send_telegram_alert(ip), app.loop)
    return jsonify({"status": "pending"})

# API: التحقق من الرد
@app.route("/check/<ip>", methods=["GET"])
def check_status(ip):
    decision = PENDING_REQUESTS.get(ip)
    return jsonify({"status": decision or "pending"})

# الدالة الرئيسية
async def main():
    app.bot_app = Application.builder().token(TOKEN).build()
    app.bot_app.add_handler(CommandHandler("start", start))
    app.bot_app.add_handler(CallbackQueryHandler(handle_decision))

    print("✅ Telegram Bot Started...")
    await app.bot_app.initialize()
    await app.bot_app.start()
    await app.bot_app.updater.start_polling()

if __name__ == "__main__":
    print("🌐 Flask API Started...")
    # شغّل Flask في Thread عادي
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000), daemon=True).start()

    # شغّل بوت تيليجرام في الـ event loop الأساسي
    asyncio.run(main())
