import os
import time
import uuid
import logging
import threading
from pathlib import Path
from urllib.parse import urlparse

import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =====================================================
# 1. الإعدادات
# =====================================================

TOKEN = "8823255880:AAFUlGDBt5HWNt6qCzrk8IkXRy3_O2xFfW4"

AD_URL = "https://uplcm.com/4/11968073"
INSTAGRAM_URL = "https://www.instagram.com/mah__asw"

WAIT_SECONDS = 10
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

if not TOKEN:
    raise RuntimeError(
        "لم يتم تعيين TELEGRAM_BOT_TOKEN. "
        "أضف توكن البوت الجديد إلى متغيرات البيئة."
    )

bot = telebot.TeleBot(TOKEN, threaded=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# =====================================================
# 2. بيانات المستخدمين
# =====================================================

pending_urls = {}
user_states = {}
ad_messages = {}
user_timers = {}
state_lock = threading.RLock()


# =====================================================
# 3. إدارة الرسائل والمؤقتات
# =====================================================

def remember_message(user_id, message):
    with state_lock:
        ad_messages.setdefault(user_id, []).append(
            (message.chat.id, message.message_id)
        )


def send_tracked(user_id, chat_id, text, **kwargs):
    message = bot.send_message(chat_id, text, **kwargs)
    remember_message(user_id, message)
    return message


def delete_ad_messages(user_id):
    with state_lock:
        messages = ad_messages.pop(user_id, [])

    for chat_id, message_id in messages:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as exc:
            logger.info("تعذر حذف الرسالة %s: %s", message_id, exc)


def cancel_user_timer(user_id):
    with state_lock:
        timer = user_timers.pop(user_id, None)
    if timer:
        timer.cancel()


def start_user_timer(user_id, seconds, callback, *args):
    cancel_user_timer(user_id)
    timer = threading.Timer(seconds, callback, args=args)
    timer.daemon = True
    with state_lock:
        user_timers[user_id] = timer
    timer.start()


def valid_url(text):
    try:
        parsed = urlparse(text.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


# =====================================================
# 4. لوحات المفاتيح (Keyboards)
# =====================================================

def create_ad_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📢 فتح الإعلان", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ شاهدت الإعلان، أؤكد المتابعة", callback_data="confirm_ad"))
    return markup


def create_next_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📥 تحميل فيديو آخر", callback_data="next_video"))
    return markup


# =====================================================
# 5. الأوامر واستقبال الروابط
# =====================================================

@bot.message_handler(commands=["start", "help"])
def start_command(message):
    user_id = message.from_user.id
    with state_lock:
        busy = user_id in pending_urls

    if busy:
        bot.reply_to(message, "⏳ لديك طلب قيد الانتظار أو التحميل. أكمل الطلب الحالي أولاً.")
        return

    text = (
        "مرحباً بك في Media Downloader Bot 🚀\n\n"
        "أرسل رابط فيديو عام من منصة مدعومة.\n\n"
        "📢 قبل التحميل، يجب فتح صفحة الإعلان ثم تأكيد المتابعة."
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=["text"], func=lambda message: not message.text.startswith("/"))
def receive_video(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    video_url = message.text.strip()

    if not valid_url(video_url):
        bot.reply_to(message, "⚠️ أرسل رابطاً صالحاً يبدأ بـ http:// أو https://")
        return

    with state_lock:
        if user_id in pending_urls:
            bot.reply_to(message, "⏳ لديك رابط سابق قيد المعالجة. انتظر حتى ينتهي.")
            return

        pending_urls[user_id] = video_url
        user_states[user_id] = "waiting_confirmation"

    try:
        send_tracked(
            user_id,
            chat_id,
            "⚠️ لتحميل الفيديو:\n\n"
            "1️⃣ اضغط على زر فتح الإعلان.\n"
            "2️⃣ ارجع إلى البوت واضغط زر التأكيد.\n\n"
            "إذا لم تؤكد خلال 10 ثوانٍ، سأذكّرك.",
            reply_markup=create_ad_keyboard()
        )

        start_user_timer(user_id, WAIT_SECONDS, send_confirmation_reminder, user_id, chat_id)

    except Exception:
        logger.exception("تعذر إرسال رسالة الإعلان.")
        with state_lock:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)
        bot.reply_to(message, "❌ تعذر إنشاء طلب التحميل. حاول مجدداً.")


def send_confirmation_reminder(user_id, chat_id):
    with state_lock:
        if user_states.get(user_id) != "waiting_confirmation":
            return
        user_timers.pop(user_id, None)

    try:
        send_tracked(
            user_id,
            chat_id,
            "⚠️ لم يتم تأكيد المتابعة بعد!\n\n"
            "شاهد الإعلان أولاً، ثم اضغط زر التأكيد.",
            reply_markup=create_ad_keyboard()
        )
    except Exception:
        logger.exception("تعذر إرسال رسالة التذكير.")


# =====================================================
# 6. المعالجة والتأكيد والتحميل
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "confirm_ad")
def confirm_ad(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    with state_lock:
        state = user_states.get(user_id)
        if user_id not in pending_urls:
            state = None

        if state == "confirmed":
            bot.answer_callback_query(call.id, "تم تأكيد طلبك مسبقاً، انتظر التحميل.")
            return
        if state == "downloading":
            bot.answer_callback_query(call.id, "التحميل قيد التنفيذ بالفعل.")
            return
        if state != "waiting_confirmation":
            bot.answer_callback_query(call.id, "أرسل رابط الفيديو أولاً.")
            return

        user_states[user_id] = "confirmed"

    cancel_user_timer(user_id)
    bot.answer_callback_query(call.id, "تم تسجيل التأكيد بنجاح.")

    try:
        send_tracked(
            user_id,
            chat_id,
            "✅ تم تسجيل التأكيد.\n\n⏳ سيبدأ التحميل تلقائياً خلال لحظات..."
        )
        start_user_timer(user_id, 3, process_download, user_id, chat_id)
    except Exception:
        logger.exception("تعذر بدء مؤقت التحميل.")
        with state_lock:
            user_states[user_id] = "waiting_confirmation"
        bot.send_message(chat_id, "❌ تعذر بدء الطلب. حاول مجدداً.")


def process_download(user_id, chat_id):
    with state_lock:
        if user_states.get(user_id) != "confirmed":
            return
        video_url = pending_urls.get(user_id)
        if not video_url:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)
            return

        user_states[user_id] = "downloading"
        user_timers.pop(user_id, None)

    request_id = uuid.uuid4().hex
    output_template = str(DOWNLOAD_DIR / f"{user_id}_{request_id}.%(ext)s")
    downloaded_file = None
    status_message = None
    success = False

    try:
        status_message = bot.send_message(chat_id, "⏳ جارٍ تحميل الفيديو، يرجى الانتظار...")

        options = {
            "outtmpl": output_template,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "max_filesize": MAX_FILE_SIZE,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "socket_timeout": 30,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = Path(ydl.prepare_filename(info))

        if not downloaded_file.exists():
            candidates = list(DOWNLOAD_DIR.glob(f"{user_id}_{request_id}.*"))
            if candidates:
                downloaded_file = candidates[0]

        if not downloaded_file.exists():
            raise FileNotFoundError("لم يتم العثور على ملف الفيديو بعد التحميل.")

        if downloaded_file.stat().st_size > MAX_FILE_SIZE:
            raise ValueError("حجم الفيديو أكبر من 50 ميغابايت المسموح بها.")

        with downloaded_file.open("rb") as video:
            bot.send_video(chat_id, video, supports_streaming=True, timeout=120)

        success = True
        logger.info("تم إرسال الفيديو للمستخدم %s بنجاح", user_id)

    except Exception as exc:
        logger.exception("فشل تنزيل الفيديو للمستخدم %s", user_id)
        try:
            bot.send_message(
                chat_id,
                f"❌ تعذر تحميل الفيديو.\nتأكد من صلاحية الرابط وأنه عام.\nالتفاصيل: {str(exc)[:300]}"
            )
        except Exception:
            pass

    finally:
        if downloaded_file and downloaded_file.exists():
            try:
                downloaded_file.unlink()
            except OSError:
                pass

        if status_message:
            try:
                bot.delete_message(chat_id, status_message.message_id)
            except Exception:
                pass

        with state_lock:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)
            user_timers.pop(user_id, None)

    if success:
        delete_ad_messages(user_id)
        try:
            bot.send_message(
                chat_id,
                "✅ تم إرسال الفيديو بنجاح.\n\nلتحميل فيديو آخر، اضغط أدناه:",
                reply_markup=create_next_keyboard()
            )
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: call.data == "next_video")
def next_video(call):
    user_id = call.from_user.id
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    bot.answer_callback_query(call.id, "أرسل رابط الفيديو الجديد الآن.")
    bot.send_message(call.message.chat.id, "📎 أرسل رابط الفيديو الجديد.")


# =====================================================
# 7. تشغيل البوت
# =====================================================

if __name__ == "__main__":
    logger.info("Media Downloader Bot is starting...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except KeyboardInterrupt:
            logger.info("تم إيقاف البوت بواسطة المستخدم.")
            break
        except Exception:
            logger.exception("انقطع الاتصال. إعادة المحاولة بعد 5 ثوانٍ...")
            time.sleep(5)
            
