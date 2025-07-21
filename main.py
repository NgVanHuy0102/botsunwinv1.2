import asyncio
import time
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7318584635:AAH-kPr0CoVzO-2bQkYg6KdS-4Be_-w2owo"
API_URL = "https://apisw-kyn6.onrender.com/predict"
ADMIN_ID = 7598401539  # 👈 THAY bằng Telegram user ID của bạn

active_keys = {}
bot_active = {}
last_sessions = {}

def is_key_valid(user_id):
    key_info = active_keys.get(user_id)
    if not key_info:
        return False
    return key_info["expire"] > time.time()

async def start_bot_loop(application, chat_id):
    while bot_active.get(chat_id, False):
        try:
            res = requests.get(API_URL).json()
            session = res.get("current_session")
            dice = res.get("current_dice", [0, 0, 0])
            result = res.get("current_result")
            total = res.get("current_total")
            du_doan = res.get("du_doan", "Không rõ")

            if all(d > 0 for d in dice) and session != last_sessions.get(chat_id):
                last_sessions[chat_id] = session
                msg = f"""📢 Kết quả mới:
• Phiên: {session}
• Kết quả: 🎲 {dice[0]} + {dice[1]} + {dice[2]} = {total} → {result}

🔮 Dự đoán phiên sau: {du_doan}"""
                await application.bot.send_message(chat_id=chat_id, text=msg)
        except Exception as e:
            print("❌ Lỗi:", e)
        await asyncio.sleep(2)

async def key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔑 Nhập key. Ví dụ: /key abcxyz")
        return
    key = context.args[0]
    expire = time.time() + 3 * 86400
    active_keys[update.effective_user.id] = {"key": key, "expire": expire}
    await update.message.reply_text("✅ Key hợp lệ! Dùng /chaybot để bắt đầu.")

async def chaybot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_key_valid(uid):
        await update.message.reply_text("❌ Key không hợp lệ hoặc đã hết hạn.")
        return

    cid = update.effective_chat.id
    if bot_active.get(cid):
        await update.message.reply_text("⚠️ Bot đã chạy.")
        return

    bot_active[cid] = True
    await update.message.reply_text("▶️ Bắt đầu theo dõi kết quả mới...")

    asyncio.create_task(start_bot_loop(context.application, cid))

async def tatbot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    bot_active[cid] = False
    await update.message.reply_text("🛑 Bot đã dừng.")

async def checkkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_key_valid(uid):
        await update.message.reply_text("❌ Chưa nhập key hoặc key đã hết hạn.")
        return
    expire = datetime.fromtimestamp(active_keys[uid]["expire"])
    await update.message.reply_text(f"🔍 Key còn hạn đến: {expire.strftime('%Y-%m-%d %H:%M:%S')}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """📘 *Hướng dẫn sử dụng Bot Tài Xỉu:*

🔑 /key <key> – Nhập key để kích hoạt bot  
▶️ /chaybot – Bắt đầu nhận kết quả  
⏹ /tatbot – Dừng nhận kết quả  
🔍 /checkkey – Kiểm tra key đang dùng  
📖 /help – Hiển thị hướng dẫn

🛠 *Dành cho Admin:*  
/taokey <user> <3d|5h> <sl>""",
        parse_mode="Markdown"
    )

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await help_cmd(update, context)

async def taokey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền tạo key.")
        return
    try:
        username = context.args[0]
        duration = context.args[1]
        limit = int(context.args[2])
        if duration.endswith("d"):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith("h"):
            seconds = int(duration[:-1]) * 3600
        else:
            raise ValueError("Sai định dạng thời gian.")
        key = f"{username}_{int(time.time())}"
        expire = time.time() + seconds
        await update.message.reply_text(f"✅ Key tạo thành công:\n`{key}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Cú pháp sai. Dùng: /taokey vanhyy 3d 5")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("key", key_cmd))
    app.add_handler(CommandHandler("chaybot", chaybot_cmd))
    app.add_handler(CommandHandler("tatbot", tatbot_cmd))
    app.add_handler(CommandHandler("checkkey", checkkey_cmd))
    app.add_handler(CommandHandler("taokey", taokey_cmd))
    print("✅ Bot đang chạy...")
    app.run_polling()
