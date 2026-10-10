
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

TOKEN = os.getenv("8823255880:AAFUlGDBt5HWNt6qCzrk8IkXRy3_O2xFfW4", "").strip()
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

# روابط الفيديو التي تنتظر المعالجة
pending_urls = {}

# الحالات:
# waiting_confirmation = ينتظر تأكيد المستخدم
# confirmed = تم التأكيد وينتظر انتهاء المؤقت
# downloading = بدأ التحميل

user_states = {}

# رسائل البوت التي يجب حذفها بعد نجاح إرسال الفيديو
ad_messages = {}

# المؤقتات النشطة
user_timers = {}

# حماية البيانات المشتركة
state_lock = threading.RLock()


# =====================================================
# 3. إدارة الرسائل والمؤقتات
# =====================================================

def remember_message(user_id, message):
    """حفظ معرّف رسالة البوت لحذفها لاحقاً."""
    with state_lock:
        ad_messages.setdefault(user_id, []).append(
            (message.chat.id, message.message_id)
        )


def send_tracked(user_id, chat_id, text, **kwargs):
    """إرسال رسالة وتسجيلها."""
    message = bot.send_message(
        chat_id,
        text,
        **kwargs
    )
    remember_message(user_id, message)
    return message


def delete_ad_messages(user_id):
    """حذف رسائل الإعلان والتذكير التي أرسلها البوت."""
    with state_lock:
        messages = ad_messages.pop(user_id, [])

    for chat_id, message_id in messages:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as exc:
            logger.info(
                "تعذر حذف الرسالة %s: %s",
                message_id,
                exc
            )


def cancel_user_timer(user_id):
    """إلغاء المؤقت السابق إن وجد."""
    with state_lock:
        timer = user_timers.pop(user_id, None)

    if timer:
        timer.cancel()


def start_user_timer(user_id, seconds, callback, *args):
    """تشغيل مؤقت جديد مع حفظه."""
    cancel_user_timer(user_id)

    timer = threading.Timer(
        seconds,
        callback,
        args=args
    )
    timer.daemon = True

    with state_lock:
        user_timers[user_id] = timer

    timer.start()


def valid_url(text):
    """التحقق الأساسي من صيغة الرابط."""
    try:
        parsed = urlparse(text.strip())

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )
    except Exception:
        return False


# =====================================================
# 4. لوحة الإعلان والتأكيد
# =====================================================

def create_ad_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    # زر يفتح صفحة الإعلان مباشرة
    markup.add(
        InlineKeyboardButton(
            "📢 فتح الإعلان",
            url=AD_URL
        )
    )

    # زر منفصل لتأكيد المتابعة
    markup.add(
        InlineKeyboardButton(
            "✅ شاهدت الإعلان، أؤكد المتابعة",
            callback_data="confirm_ad"
        )
    )

    return markup


def create_next_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(
        InlineKeyboardButton(
            "📥 تحميل فيديو آخر",
            callback_data="next_video"
        )
    )

    return markup


# =====================================================
# 5. أمر البداية
# =====================================================

@bot.message_handler(commands=["start", "help"])
def start_command(message):
    user_id = message.from_user.id

    with state_lock:
        busy = user_id in pending_urls

    if busy:
        bot.reply_to(
            message,
            "⏳ لديك طلب قيد الانتظار أو التحميل. "
            "أكمل الطلب الحالي أولاً."
        )
        return

    text = (
        "مرحباً بك في Media Downloader Bot 🚀\n\n"
        "أرسل رابط فيديو عام من منصة مدعومة.\n\n"
        "📢 قبل التحميل، يجب فتح صفحة الإعلان "
        "ثم تأكيد المتابعة من الزر المخصص."
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =====================================================
# 6. استقبال رابط الفيديو
# =====================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: not message.text.startswith("/")
)
def receive_video(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    video_url = message.text.strip()

    if not valid_url(video_url):
        bot.reply_to(
            message,
            "⚠️ أرسل رابطاً صالحاً يبدأ بـ "
            "http:// أو https://"
        )
        return

    with state_lock:
        if user_id in pending_urls:
            bot.reply_to(
                message,
                "⏳ لديك رابط سابق قيد المعالجة. "
                "انتظر حتى ينتهي قبل إرسال رابط جديد."
            )
            return

        pending_urls[user_id] = video_url
        user_states[user_id] = "waiting_confirmation"

    # إرسال رسالة الإعلان الإجباري
    try:
        send_tracked(
            user_id,
            chat_id,
            "⚠️ لتحميل الفيديو:\n\n"
            "1️⃣ اضغط على زر فتح الإعلان.\n"
            "2️⃣ ارجع إلى البوت واضغط زر التأكيد.\n\n"
            "إذا لم تؤكد خلال 10 ثوانٍ، "
            "سأذكّرك بمشاهدة الإعلان والتأكيد.\n"
            "لن يبدأ التحميل دون التأكيد.",
            reply_markup=create_ad_keyboard()
        )

        # بعد 10 ثوانٍ: التذكير فقط، وليس التحميل
        start_user_timer(
            user_id,
            WAIT_SECONDS,
            send_confirmation_reminder,
            user_id,
            chat_id
        )

    except Exception:
        logger.exception("تعذر إرسال رسالة الإعلان.")

        with state_lock:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)

        bot.reply_to(
            message,
            "❌ تعذر إنشاء طلب التحميل. حاول مجدداً."
        )


# =====================================================
# 7. التذكير عند عدم التأكيد خلال 10 ثوانٍ
# =====================================================

def send_confirmation_reminder(user_id, chat_id):
    with state_lock:
        # لا نرسل التذكير إن كان المستخدم قد أكد أو بدأ التحميل
        if user_states.get(user_id) != "waiting_confirmation":
            return

        # انتهى المؤقت الأول
        user_timers.pop(user_id, None)

    try:
        send_tracked(
            user_id,
            chat_id,
            "⚠️ لم يتم تأكيد المتابعة بعد!\n\n"
            "شاهد الإعلان أولاً، ثم ارجع إلى البوت "
            "واضغط زر:\n"
            "✅ شاهدت الإعلان، أؤكد المتابعة\n\n"
            "لن يتم تحميل الفيديو قبل التأكيد.",
            reply_markup=create_ad_keyboard()
        )
    except Exception:
        logger.exception("تعذر إرسال رسالة التذكير.")


# =====================================================
# 8. تأكيد المستخدم
# =====================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "confirm_ad"
)
def confirm_ad(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    with state_lock:
        state = user_states.get(user_id)

        if user_id not in pending_urls:
            state = None

        if state == "confirmed":
            bot.answer_callback_query(
                call.id,
                "تم تأكيد طلبك، انتظر التحميل."
            )
            return

        if state == "downloading":
            bot.answer_callback_query(
                call.id,
                "التحميل قيد التنفيذ."
            )
            return

        if state != "waiting_confirmation":
            bot.answer_callback_query(
                call.id,
                "أرسل رابط الفيديو أولاً."
            )
            return

        # تسجيل التأكيد
        user_states[user_id] = "confirmed"

    # إلغاء مؤقت التذكير
    cancel_user_timer(user_id)

    bot.answer_callback_query(
        call.id,
        "تم تسجيل التأكيد. انتظر 10 ثوانٍ."
    )

    try:
        send_tracked(
            user_id,
            chat_id,
            "✅ تم تسجيل التأكيد.\n\n"
            "⏳ جارٍ تجهيز طلبك، "
            "سيبدأ التحميل تلقائياً بعد 10 ثوانٍ."
        )

        # بعد التأكيد ننتظر 10 ثوانٍ ثم نبدأ التحميل
        start_user_timer(
            user_id,
            WAIT_SECONDS,
            process_download,
            user_id,
            chat_id
        )

    except Exception:
        logger.exception("تعذر بدء مؤقت التحميل.")

        with state_lock:
            user_states[user_id] = "waiting_confirmation"

        bot.send_message(
            chat_id,
            "❌ تعذر بدء الطلب. حاول الضغط على التأكيد مجدداً."
        )


# =====================================================
# 9. تنزيل الفيديو
# =====================================================

def process_download(user_id, chat_id):
    with state_lock:
        if user_states.get(user_id) != "confirmed":
            return

        video_url = pending_urls.get(user_id)

        if not video_url:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)
            return

        # منع بدء التحميل مرتين
        user_states[user_id] = "downloading"
        user_timers.pop(user_id, None)

    request_id = uuid.uuid4().hex

    output_template = str(
        DOWNLOAD_DIR /
        f"{user_id}_{request_id}.%(ext)s"
    )

    downloaded_file = None
    status_message = None
    success = False

    try:
        status_message = bot.send_message(
            chat_id,
            "⏳ جارٍ تحميل الفيديو، يرجى الانتظار..."
        )

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
            info = ydl.extract_info(
                video_url,
                download=True
            )

            downloaded_file = Path(
                ydl.prepare_filename(info)
            )

        # البحث عن الملف إذا تغير امتداده
        if not downloaded_file.exists():
            candidates = list(
                DOWNLOAD_DIR.glob(
                    f"{user_id}_{request_id}.*"
                )
            )

            if candidates:
                downloaded_file = candidates[0]

        if not downloaded_file.exists():
            raise FileNotFoundError(
                "لم يتم العثور على ملف الفيديو."
            )

        file_size = downloaded_file.stat().st_size

        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                "حجم الفيديو أكبر من 50 ميغابايت."
            )

        # إرسال محتوى الرابط
        with downloaded_file.open("rb") as video:
            bot.send_video(
                chat_id,
                video,
                supports_streaming=True,
                timeout=120
            )

        success = True

        logger.info(
            "تم إرسال الفيديو للمستخدم %s",
            user_id
        )

    except Exception as exc:
        logger.exception(
            "فشل تنزيل الفيديو للمستخدم %s",
            user_id
        )

        try:
            bot.send_message(
                chat_id,
                "❌ تعذر تحميل الفيديو.\n\n"
                "تأكد من صلاحية الرابط وأنه عام، "
                "وأن حجمه ضمن الحد المسموح.\n\n"
                f"التفاصيل: {str(exc)[:500]}"
            )
        except Exception:
            logger.exception("تعذر إرسال رسالة الخطأ.")

    finally:
        # حذف الملف المؤقت
        if downloaded_file and downloaded_file.exists():
            try:
                downloaded_file.unlink()
            except OSError:
                logger.exception(
                    "تعذر حذف الملف المؤقت."
                )

        # حذف رسالة التحميل المؤقتة
        if status_message:
            try:
                bot.delete_message(
                    chat_id,
                    status_message.message_id
                )
            except Exception:
                pass

        # تحرير حالة المستخدم
        with state_lock:
            pending_urls.pop(user_id, None)
            user_states.pop(user_id, None)
            user_timers.pop(user_id, None)

    if success:
        # حذف رسائل الإعلان والتذكير بعد إرسال الفيديو
        delete_ad_messages(user_id)

        try:
            bot.send_message(
                chat_id,
                "✅ تم تحميل الفيديو وإرساله بنجاح.\n\n"
                "لتحميل فيديو آخر، أرسل رابطه.",
                reply_markup=create_next_keyboard()
            )
        except Exception:
            logger.exception(
                "تعذر إرسال رسالة إتمام التحميل."
            )


# =====================================================
# 10. زر طلب فيديو جديد
# =====================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "next_video"
)
def next_video(call):
    user_id = call.from_user.id

    with state_lock:
        busy = user_id in pending_urls

    if busy:
        bot.answer_callback_query(
            call.id,
            "لديك طلب قيد المعالجة."
        )
        return

    bot.answer_callback_query(
        call.id,
        "أرسل رابط الفيديو الجديد."
    )

    bot.send_message(
        call.message.chat.id,
        "📎 أرسل رابط الفيديو الجديد."
    )


# =====================================================
# 11. تشغيل البوت وإعادة الاتصال
# =====================================================

if __name__ == "__main__":
    logger.info("Media Downloader Bot is starting...")

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )

        except KeyboardInterrupt:
            logger.info("تم إيقاف البوت.")
            break

        except Exception:
            logger.exception(
                "انقطع الاتصال. إعادة المحاولة بعد 5 ثوانٍ."
            )
            time.sleep(5)
            
