import asyncio
import logging
import os
import random
import re
import threading
from typing import List, Optional

import telebot
from telebot import types

try:
    from TikTokLive import TikTokLiveClient
except Exception:  # pragma: no cover
    TikTokLiveClient = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    logging.warning("TELEGRAM_BOT_TOKEN is empty. Bot will not connect until configured.")

bot = telebot.TeleBot(TOKEN, parse_mode=None) if TOKEN else None
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.txt")
MAX_PARALLEL_ACTIONS = int(os.getenv("MAX_PARALLEL_ACTIONS", "3"))

RANDOM_COMMENTS = [
    "🔥 أكشن حلو جدًا!",
    "💪 دعم ممتاز!",
    "👏 بث رائع!",
    "✨ استمر يارب!",
    "🎉 مجهود رائع!",
    "🔥 متابعة دايمًا!",
    "❤️ حلو جدًا!",
    "👍 رائع جدًا!",
    "💥 ممتاز جدًا!",
    "🎯 تفاعل قوي!",
]

_ACTIVE_THREADS: List[threading.Thread] = []


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


def normalize_target(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    text = text.replace("@", "")

    if "tiktok.com" in text.lower():
        match = re.search(r"tiktok\.com/@?([A-Za-z0-9._-]+)", text, re.I)
        if match:
            return match.group(1).strip("/")

    text = text.split("?", 1)[0]
    text = text.split("#", 1)[0]
    text = text.strip("/")
    text = re.sub(r"^https?://", "", text)
    text = text.replace("www.", "")
    text = text.replace("m.", "")

    return text.strip()


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
    if bot is None:
        return

    markup = build_main_menu()
    bot.send_message(
        message.chat.id,
        "🤖 أهلاً بك في لوحة تحكم تيك توك الاحترافية.\n"
        "اختر أي أمر من الأزرار أدناه:\n\n"
        "⚡ تكبيس\n"
        "💬 تعليقات عشوائية\n"
        "✍️ تعليق موحد\n"
        "➕ إضافة جلسة حساب\n"
        "📊 عدد الحسابات\n"
        "🗑️ حذف جلسة",
        reply_markup=markup,
    )


@bot.message_handler(commands=['status', 'info'])
def status_command(message):
    if bot is None:
        return

    accounts = load_accounts()
    bot.send_message(
        message.chat.id,
        f"📊 حالة البوت:\n"
        f"- عدد الجلسات المحفوظة: {len(accounts)}\n"
        f"- TELEGRAM TOKEN: {'مفعّل' if bool(TOKEN) else 'غير مفعّل'}\n"
        f"- TikTokLive: {'موجود' if TikTokLiveClient else 'غير موجود'}\n"
        f"- أقصى مهام متزامنة: {MAX_PARALLEL_ACTIONS}",
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if bot is None:
        return

    text = (message.text or "").strip()

    if text == "⚡ ( تكبيس )":
        msg = bot.send_message(message.chat.id, "🚀 أرسل رابط البث المباشر أو اسم المستخدم الكامل الآن:")
        bot.register_next_step_handler(msg, execute_tapping_task)

    elif text == "💬 ( تعليقات عشوائية )":
        msg = bot.send_message(message.chat.id, "💬 أرسل رابط البث المباشر أو اسم المستخدم الكامل الآن:")
        bot.register_next_step_handler(msg, execute_random_comment_task)

    elif text == "✍️ ( تعليق موحد )":
        msg = bot.send_message(message.chat.id, "✍️ أرسل نص التعليق الموحد الآن، ثم رابط البث أو اسم المستخدم:")
        bot.register_next_step_handler(msg, get_comment_text)

    elif text == "➕ ( إضافة جلسة حساب )":
        msg = bot.send_message(
            message.chat.id,
            "➕ أرسل نص الجلسة / Session / Cookie / Token.\nيمكنك إرسال أي نص يدعم الجلسة من 5 أحرف فأكثر.",
        )
        bot.register_next_step_handler(msg, save_session_step)

    elif text == "📊 ( عدد الحسابات )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة حتى الآن.")
        else:
            bot.send_message(message.chat.id, f"📊 عدد الحسابات المحفوظة: {len(accounts)}")

    elif text == "🗑️ ( حذف جلسة )":
        accounts = load_accounts()
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لا توجد جلسات للحذف.")
            return

        response = "🗑️ اختر رقم الجلسة المراد حذفها:\n\n"
        for i, acc in enumerate(accounts, 1):
            short = acc[:18] + "..." if len(acc) > 18 else acc
            response += f"{i} - {short}\n"
        response += "\nأرسل الرقم فقط الآن:"
        msg = bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(msg, delete_session_step)


def save_session_step(message):
    if bot is None:
        return

    session_text = (message.text or "").strip()
    if len(session_text) < 5:
        bot.send_message(message.chat.id, "❌ النص قصير جداً. أعد المحاولة.")
        return

    if save_account(session_text):
        bot.send_message(message.chat.id, "✅ تم حفظ الجلسة بنجاح في ملف accounts.txt")
    else:
        bot.send_message(message.chat.id, "⚠️ هذه الجلسة موجودة مسبقاً أو غير صالحة.")


def delete_session_step(message):
    if bot is None:
        return

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
    if bot is None:
        return

    comment = (message.text or "").strip()
    if not comment:
        bot.send_message(message.chat.id, "❌ التعليق فارغ. أعد المحاولة.")
        return

    msg = bot.send_message(
        message.chat.id,
        f"📝 تم اعتماد التعليق: {comment}\n\nالآن ارسل رابط البث أو اسم المستخدم الكامل:",
    )
    bot.register_next_step_handler(msg, execute_comment_task, comment)


def execute_tapping_task(message):
    if bot is None:
        return

    target_user = normalize_target(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ الرابط أو اسم المستخدم غير صحيح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة، أضف جلسة أولاً.")
        return

    bot.send_message(
        message.chat.id,
        f"⚡ جاري تنفيذ التكبيس على البث @{target_user} عبر {len(accounts)} جلسة محفوظة...",
    )
    queue_live_action_for_all(accounts, target_user, "like")


def execute_random_comment_task(message):
    if bot is None:
        return

    target_user = normalize_target(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ الرابط أو اسم المستخدم غير صحيح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة. أضف جلسة أولاً.")
        return

    comment = random.choice(RANDOM_COMMENTS)
    bot.send_message(
        message.chat.id,
        f"💬 جاري إرسال تعليق عشوائي على @{target_user}: \"{comment}\"",
    )
    queue_live_action_for_all(accounts, target_user, "comment", comment)


def execute_comment_task(message, comment: str):
    if bot is None:
        return

    target_user = normalize_target(message.text)
    if not target_user:
        bot.send_message(message.chat.id, "❌ الرابط أو اسم المستخدم غير صحيح.")
        return

    accounts = load_accounts()
    if not accounts:
        bot.send_message(message.chat.id, "⚠️ لا توجد جلسات محفوظة. أضف جلسة أولاً.")
        return

    bot.send_message(
        message.chat.id,
        f"✍️ جاري إرسال التعليق الموحد على @{target_user}: \"{comment}\"",
    )
    queue_live_action_for_all(accounts, target_user, "comment", comment)


def queue_live_action_for_all(accounts: List[str], target_user: str, action: str, comment: Optional[str] = None) -> None:
    running = [t for t in _ACTIVE_THREADS if t.is_alive()]
    if len(running) >= MAX_PARALLEL_ACTIONS:
        logging.warning("Max parallel actions reached. Skipping extra tasks.")
        return

    for session in accounts:
        thread = threading.Thread(
            target=run_live_action_worker,
            args=(session, target_user, action, comment),
            daemon=True,
        )
        _ACTIVE_THREADS.append(thread)
        thread.start()


def _safe_call_method(instance, method_names, *args):
    for name in method_names:
        method = getattr(instance, name, None)
        if callable(method):
            try:
                return method(*args)
            except TypeError:
                try:
                    return method()
                except Exception:
                    raise
    return None


async def perform_tiktok_live_action(session_value: str, target_user: str, action: str, comment: Optional[str] = None) -> None:
    if TikTokLiveClient is None:
        raise RuntimeError("TikTokLive library is not installed.")

    client = TikTokLiveClient(unique_id=target_user)
    client.session_value = session_value

    try:
        connect_method = getattr(client, "connect", None) or getattr(client, "start", None)
        if callable(connect_method):
            await connect_method()
        else:
            raise AttributeError("TikTokLiveClient has no connect() or start() method.")

        await asyncio.sleep(1.2)

        if action == "like":
            result = _safe_call_method(client, ("like", "send_like", "send_like_event", "heart"))
            if result is not None and asyncio.iscoroutine(result):
                await result

        elif action == "comment":
            final_comment = comment or random.choice(RANDOM_COMMENTS)
            result = _safe_call_method(client, ("comment", "send_comment", "post_comment"), final_comment)
            if result is not None and asyncio.iscoroutine(result):
                await result

    except Exception as exc:
        logging.exception("TikTok live action failed: %s", exc)
        raise
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
        logging.exception(
            "TikTok live action failed for session=%s target=%s action=%s error=%s",
            session_value[:20],
            target_user,
            action,
            exc,
        )
    finally:
        for thread in list(_ACTIVE_THREADS):
            if not thread.is_alive():
                _ACTIVE_THREADS.remove(thread)


if __name__ == "__main__":
    ensure_accounts_file()
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is missing. Set it in environment variables before launching.")
        raise SystemExit(1)

    print("TikTok Python Bot is running...")
    bot.infinity_polling(timeout=60, interval=0.5, skip_pending=True)
