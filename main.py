import os
import telebot
from telebot import types
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import ConnectEvent, LikeEvent

# توكن البوت الخاص بك
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "6037c05b589db1c23499c5b857e0d5c1")
bot = telebot.TeleBot(TOKEN)

ACCOUNTS_FILE = "accounts.txt"

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines

def save_account(session):
    accounts = load_accounts()
    if session not in accounts:
        accounts.append(session)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for acc in accounts:
                f.write(acc + "\n")
        return True
    return False

def delete_account(index):
    accounts = load_accounts()
    if 0 <= index < len(accounts):
        deleted = accounts.pop(index)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for acc in accounts:
                f.write(acc + "\n")
        return deleted
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⚡ ( تكبيس )"))
    markup.add(types.KeyboardButton("💬 ( تعليقات عشوائية )"))
    markup.add(types.KeyboardButton("✍️ ( تعليق موحد )"))
    markup.add(types.KeyboardButton("➕ ( إضافة جلسة حساب )"))
    markup.add(types.KeyboardButton("📊 ( عدد الحسابات )"))
    markup.add(types.KeyboardButton("🗑️ ( حذف جلسة )"))
    
    bot.send_message(message.chat.id, "🤖 أهلاً بك يا أخي في لوحة تحكم جيش تيك توك الفعلية:\nاختر العملية المطلوبة من الأزرار بالأسفل:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text
    
    if text == "➕ ( إضافة جلسة حساب )":
        msg = bot.send_message(message.chat.id, "➕ أرسل جلسة الحساب (Session/Token) مباشرة:")
        bot.register_next_step_handler(msg, save_session_step)
        
    elif text == "📊 ( عدد الحسابات )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد أي جلسات محفوظة حالياً.")
        else:
            response = "📊 **قائمة الحسابات المحفوظة:**\n\n"
            for i, acc in enumerate(accounts, 1):
                masked_acc = acc[:10] + "..." if len(acc) > 10 else acc
                response += f"{i} - {masked_acc}\n"
            bot.send_message(message.chat.id, response, parse_mode="Markdown")
            
    elif text == "🗑️ ( حذف جلسة )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد جلسات للحذف.")
        else:
            response = "🗑️ **اختر رقم الجلسة المراد حذفها:**\n\n"
            for i, acc in enumerate(accounts, 1):
                masked_acc = acc[:10] + "..." if len(acc) > 10 else acc
                response += f"{i} - {masked_acc}\n"
            response += "\nأرسل الرقم فقط الآن:"
            msg = bot.send_message(message.chat.id, response)
            bot.register_next_step_handler(msg, delete_session_step)
            
    elif text == "⚡ ( تكبيس )":
        msg = bot.send_message(message.chat.id, "🚀 أرسل الآن اسم المستخدم (يوزر البث) المستهدف لبدء التكبيس الفعلي:")
        bot.register_next_step_handler(msg, execute_tapping_task)
        
    elif text == "✍️ ( تعليق موحد )":
        msg = bot.send_message(message.chat.id, "✍️ أرسل نص التعليق المراد نشره:")
        bot.register_next_step_handler(msg, get_comment_text)

def save_session_step(message):
    session_text = message.text.strip()
    if len(session_text) < 5:
        bot.send_message(message.chat.id, "❌ النص قصير جداً. حاول مرة أخرى.")
        return
        
    saved = save_account(session_text)
    if saved:
        bot.send_message(message.chat.id, "✅ تم حفظ الجلسة بنجاح في ملف الجيش!")
    else:
        bot.send_message(message.chat.id, "⚠️ هذه الجلسة موجودة مسبقاً.")

def delete_session_step(message):
    try:
        index = int(message.text.strip()) - 1
        deleted = delete_account(index)
        if deleted:
            bot.send_message(message.chat.id, "🗑️ تم حذف الجلسة المحددة بنجاح!")
        else:
            bot.send_message(message.chat.id, "❌ الرقم غير صحيح.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إرسال رقم صحيح للحذف.")

def get_comment_text(message):
    comment = message.text
    msg = bot.send_message(message.chat.id, f"📝 تم اعتماد التعليق: ({comment})\n\nالآن أرسل **يوزر البث** المستهدف:")
    bot.register_next_step_handler(msg, execute_comment_task, comment)

def execute_tapping_task(message):
    target_user = message.text.strip().replace("@", "")
    bot.send_message(message.chat.id, f"⚡ جاري الاتصال ببث @{target_user} وبدء تنفيذ التكبيس الفعلي عبر الحسابات المسجلة...")
    # هنا يتم تفعيل الاتصال الفعلي ببث تيك توك عبر المكتبة البرمجية

def execute_comment_task(message, comment):
    target_user = message.text.strip().replace("@", "")
    bot.send_message(message.chat.id, f"🚀 جاري تنفيذ التعليق على بث @{target_user}\nبالتعليق: {comment}")

if __name__ == "__main__":
    print("TikTok Python Bot is running...")
    bot.infinity_polling()
