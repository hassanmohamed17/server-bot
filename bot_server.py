import asyncio
import logging
from flask import Flask, request, jsonify
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

# بوت التليجرام
telegram_app = Application.builder().token(TOKEN).build()

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

# إرسال الإشعار
async def send_telegram_alert(ip):
    if AUTHORIZED_CHAT_ID is None:
        print("❌ لم يتم تسجيل أي مستخدم بعد.")
        return
    keyboard = [
        [
            InlineKeyboardButton("✅ سماح", callback_data=f"{ip}:allowed"),
            InlineKeyboardButton("❌ رفض", callback_data=f"{ip}:denied"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await telegram_app.bot.send_message(
            chat_id=AUTHORIZED_CHAT_ID,
            text=f"⚠️ محاولة تشغيل جديدة من الجهاز IP: {ip}\nهل تسمح بالتشغيل؟",
            reply_markup=reply_markup,
        )
    except Exception as e:
        print(f"❌ فشل إرسال الرسالة إلى Telegram: {e}")

# API: طلب الإذن
@app.route("/request", methods=["POST"])
def request_access():
    data = request.get_json()
    ip = data.get("ip")
    print(f"🚀 طلب تشغيل من IP: {ip}")
    PENDING_REQUESTS[ip] = None
    asyncio.create_task(send_telegram_alert(ip))  # إرسال الطلب عبر تليجرام
    return jsonify({"status": "pending"})

# API: التحقق من الإذن
@app.route("/check/<ip>", methods=["GET"])
def check_status(ip):
    decision = PENDING_REQUESTS.get(ip)
    return jsonify({"status": decision or "pending"})

# Main
if __name__ == "__main__":
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_decision))

    # تشغيل بوت تليجرام في نفس الـ loop
    loop = asyncio.get_event_loop()
    loop.create_task(telegram_app.run_polling(close_loop=False))

    print("✅ Telegram Bot Started...")
    print("🌐 Flask API Started...")
    app.run(host="0.0.0.0", port=8000)
