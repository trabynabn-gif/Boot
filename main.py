import asyncio
import logging
import os
import random
import threading
from typing import List, Optional

import telebot
from telebot import types

try:
    from TikTokLive import TikTokLiveClient
except Exception:  # pragma: no cover
    TikTokLiveClient = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "6037c05b589db1c23499c5b857e0d5c1")
bot = telebot.TeleBot(TOKEN, parse_mode=None)

ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.txt")
RANDOM_COMMENTS = [
    "🔥 أكشن حلو جدًا!",
    "💪 دعم ممتاز!",
    "👏 بث رائع!",
    "✨ استمر يارب!",
    "🎉 مجهود رائع!",
    "🔥 متابعة دايمًا!",
    "❤️ حلو جدًا!",
    "👍 رائع جدًا!",
]


def ensure_accounts_file() -> None:
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            f.write("")


def load_accounts() -> List[str]:
    ensure_accounts_file()
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_account(session: str) -> bool:
    session = (session or "").strip()
    if len(session) < 5:
        return False
    accounts = load_accounts()
    if session in accounts:
        return False
    accounts.append(session)
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        for acc in accounts:
            f.write(acc + "\n")
    return True


def delete_account(index: int) -> Optional[str]:
    accounts = load_accounts()
    if 0 <= index < len(accounts):
        deleted = accounts.pop(index)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for acc in accounts:
                f.write(acc + "\n")
        return deleted
    return None


def normalize_username(value: str) -> str:
    cleaned = (value or "").strip().replace("@", "").replace("https://www.tiktok.com/@", "")
    return cleaned.strip("/")


def build_main_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(
        types.KeyboardButton("⚡ ( تكبيس )"),
        types.KeyboardButton("💬 ( تعليقات عشوائية )"),
    )
    markup.row(
        types.KeyboardButton("✍️ ( تعليق موحد )"),
        types.KeyboardButton("➕ ( إضافة جلسة حساب )"),
    )
    markup.row(
        types.KeyboardButton("📊 ( عدد الحسابات )"),
        types.KeyboardButton("🗑️ ( حذف جلسة )"),
    )
    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = build_main_menu()
    bot.send_message(
        message.chat.id,
        "🤖 أهلاً بك في لوحة تحكم تيك توك الآمنة.\n"
        "اختر أي أمر من الأزرار الموجودة أدناه:\n\n"
        "⚡ تكبيس\n"
        "💬 تعليقات عشوائية\n"
        "✍️ تعليق موحد\n"
        "➕ إضافة جلسة حساب\n"
        "📊 عدد الحسابات\n"
        "🗑️ حذف جلسة",
        reply_markup=markup,
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = (message.text or "").strip()

    if text == "⚡ ( تكبيس )":
        msg = bot.send_message(message.chat.id, "🚀 أرسل اسم المستخدم (يوزر البث) المستهدف الآن:")
        bot.register_next_step_handler(msg, execute_tapping_task)

    elif text == "💬 ( تعليقات عشوائية )":
        msg = bot.send_message(message.chat.id, "💬 أرسل اسم المستخدم (يوزر البث) المستهدف الآن:")
        bot.register_next_step_handler(msg, execute_random_comment_task)

    elif text == "✍️ ( تعليق موحد )":
        msg = bot.send_message(message.chat.id, "✍️ أرسل نص التعليق الموحد الذي تريد إرساله:")
        bot.register_next_step_handler(msg, get_comment_text)

    elif text == "➕ ( إضافة جلسة حساب )":
        msg = bot.send_message(
            message.chat.id,
            "➕ أرسل جلسة الحساب / Session / Cookie / Token مباشرة، ويمكنك إرسال أي نص بيانات الجلسة المكون من 5 أحرف فأكثر:",
        )
        bot.register_next_step_handler(msg, save_session_step)

    elif text == "📊 ( عدد الحسابات )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد أي جلسات محفوظة حالياً.")
        else:
            bot.send_message(message.chat.id, f"📊 عدد الحسابات المحفوظة: {len(accounts)}")

    elif text == "🗑️ ( حذف جلسة )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد جلسات للحذف.")
            return

        response = "🗑️ اختر رقم الجلسة المراد حذفها:\n\n"
        for i, acc in enumerate(accounts, 1):
            short = acc[:20] + "..." if len(acc) > 20 else acc
            response += f"{i} - {short}\n"
        response += "\n��رسل الرقم فقط الآن:"
        msg = bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(msg, delete_session_step)


def save_session_step(message):
    session_text = (message.text or "").strip()
    if len(session_text) < 5:
        bot.send_message(message.chat.id, "❌ النص قصير جداً. أعد الإرسال بصيغة بيانات الجلسة الصحيحة.")
        return

    if save_account(session_text):
        bot.send_message(message.chat.id, "✅ تم حفظ الجلسة بنجاح في ملف accounts.txt")
    else:
        bot.send_message(message.chat.id, "⚠️ هذه الجلسة موجودة مسبقاً أو غير صالحة.")


def delete_session_step(message):
    try:
        index = int((message.text or "").strip()) - 1
        deleted = delete_account(index)
        if deleted is not None:
            bot.send_message(message.chat.id, "🗑️ تم حذف الجلسة المحددة بنجاح.")
        else:
            bot.send_message(message.chat.id, "❌ الرقم غير صحيح. حاول مرة أخرى.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إرسال رقم صحيح فقط.")


def get_comment_text(message):
    comment = (message.text or "").strip()
    if not comment:
        bot.send_message(message.chat.id, "❌ التعليق فارغ. أعد المحاولة.")
        return
    msg = bot.send_message(message.chat.id, f"📝 تم اعتماد التعليق: {comment}\n\nالآن أرسل اسم المستخدم (يوزر البث) المستهدف:")
    bot.register_next_step_handler(msg, execute_comment_task, comment)


def execute_tapping_task(message):
    target_user = normalize_username(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ اسم المستخدم غير صالح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة، أضف جلسة أولاً من زر (➕ إضافة جلسة حساب).")
        return

    bot.send_message(
        message.chat.id,
        f"⚡ جاري تنفيذ التكبيس على بث @{target_user} عبر {len(accounts)} جلسة محفوظة...",
    )
    for session in accounts:
        thread = threading.Thread(
            target=run_live_action_worker,
            args=(session, target_user, "like", None),
            daemon=True,
        )
        thread.start()


def execute_random_comment_task(message):
    target_user = normalize_username(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ اسم المستخدم غير صالح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة، أضف جلسة أولاً.")
        return

    comment = random.choice(RANDOM_COMMENTS)
    bot.send_message(
        message.chat.id,
        f"💬 جاري إرسال تعليق عشوائي على بث @{target_user}: \"{comment}\"",
    )
    for session in accounts:
        thread = threading.Thread(
            target=run_live_action_worker,
            args=(session, target_user, "comment", comment),
            daemon=True,
        )
        thread.start()


def execute_comment_task(message, comment: str):
    target_user = normalize_username(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ اسم المستخدم غير صالح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة، أضف جلسة أولاً.")
        return

    bot.send_message(
        message.chat.id,
        f"✍️ جاري إرسال تعليق موحد على بث @{target_user}: \"{comment}\"",
    )
    for session in accounts:
        thread = threading.Thread(
            target=run_live_action_worker,
            args=(session, target_user, "comment", comment),
            daemon=True,
        )
        thread.start()


async def perform_tiktok_live_action(session_value: str, target_user: str, action: str, comment: Optional[str] = None) -> None:
    if TikTokLiveClient is None:
        raise RuntimeError("TikTokLive library is not installed or import failed.")

    client = TikTokLiveClient(unique_id=target_user)
    client.session_value = session_value

    # هذا الحقل يتيح التعامل المباشر مع بيانات الجلسة في الأنظمة التي تدعم التحميل من ملف Session/String.
    # إذا كانت مكتبة TikTokLive تحتاج وسيط جلسة إضافي في المستقبل، يمكن تمريره هنا من خلال إعدادات العميل.
    _ = client

    try:
        if hasattr(client, "connect"):
            await client.connect()
        elif hasattr(client, "start"):
            await client.start()
        else:
            # بعض الإصدارات تستخدم run() مع async; إذا لم توجد طريقة connect/start نقوم برمي خطأ واضح.
            raise AttributeError("TikTokLiveClient does not expose connect() or start()")

        await asyncio.sleep(1.5)

        if action == "like":
            method = None
            for candidate in ("like", "send_like"):
                if hasattr(client, candidate):
                    method = getattr(client, candidate)
                    break
            if method is not None:
                await method()

        elif action == "comment":
            final_comment = comment or random.choice(RANDOM_COMMENTS)
            method = None
            for candidate in ("send_comment", "comment"):
                if hasattr(client, candidate):
                    method = getattr(client, candidate)
                    break
            if method is not None:
                await method(final_comment)

    finally:
        disconnect = getattr(client, "disconnect", None)
        if callable(disconnect):
            try:
                await disconnect()
            except Exception:
                pass


def run_live_action_worker(session_value: str, target_user: str, action: str, comment: Optional[str] = None) -> None:
    try:
        asyncio.run(perform_tiktok_live_action(session_value, target_user, action, comment))
    except Exception as exc:
        logging.exception("TikTok live action failed for %s / %s: %s", session_value[:20], target_user, exc)


if __name__ == "__main__":
    ensure_accounts_file()
    print("TikTok Python Bot is running...")
    bot.send_message = bot.send_message
    bot.infinity_polling(timeout=60, interval=0.5, skip_pending=True)
