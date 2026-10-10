
import os
import time
import uuid
import threading
import logging
from pathlib import Path
from urllib.parse import urlparse

import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# 1. الإعدادات الأساسية
# =========================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

WAIT_SECONDS = 10
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

if not TOKEN:
    raise RuntimeError(
        "لم يتم تعيين TELEGRAM_BOT_TOKEN. "
        "ضع توكن البوت في متغير البيئة أولاً."
    )

bot = telebot.TeleBot(TOKEN, threaded=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# 2. تخزين حالة المستخدمين
# =========================================================

# الرابط الذي ينتظر التحميل لكل مستخدم
pending_urls = {}

# رسائل البوت التي نريد حذفها بعد انتهاء الطلب
bot_messages = {}

# المستخدمون الذين بدأوا عملية الانتظار أو التحميل
active_jobs = set()

# قفل لحماية البيانات المشتركة
state_lock = threading.RLock()


# =========================================================
# 3. أدوات مساعدة
# =========================================================

def remember_message(user_id, message):
    """تسجيل رسالة أرسلها البوت ليتم حذفها لاحقاً."""
    with state_lock:
        bot_messages.setdefault(user_id, []).append(
            (message.chat.id, message.message_id)
        )


def send_tracked_message(user_id, chat_id, text, **kwargs):
    """إرسال رسالة وتسجيلها للحذف لاحقاً."""
    message = bot.send_message(chat_id, text, **kwargs)
    remember_message(user_id, message)
    return message


def delete_tracked_messages(user_id):
    """حذف رسائل البوت المسجلة لهذا المستخدم."""
    with state_lock:
        messages = bot_messages.pop(user_id, [])

    for chat_id, message_id in messages:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as exc:
            logger.debug(
                "تعذر حذف الرسالة %s: %s",
                message_id,
                exc
            )


def valid_http_url(text):
    """التحقق الأساسي من أن النص رابط HTTP أو HTTPS."""
    try:
        parsed = urlparse(text.strip())
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )
    except Exception:
        return False


def clear_job(user_id):
    """إنهاء حالة الطلب وإتاحة استقبال رابط جديد."""
    with state_lock:
        pending_urls.pop(user_id, None)
        active_jobs.discard(user_id)


# =========================================================
# 4. إنشاء الأزرار
# =========================================================

def instagram_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(
        InlineKeyboardButton(
            "📸 تابعنا على إنستغرام",
            url=INSTAGRAM_URL
        )
    )

    markup.add(
        InlineKeyboardButton(
            "✅ متابعة",
            callback_data="continue_download"
        )
    )

    return markup


def ad_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(
        InlineKeyboardButton(
            "📢 اضغط هنا لفتح الإعلان",
            url=AD_URL
        )
    )

    return markup


def next_video_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(
        InlineKeyboardButton(
            "📥 تحميل فيديو آخر",
            callback_data="next_video"
        )
    )

    return markup


# =========================================================
# 5. أوامر البداية والمساعدة
# =========================================================

@bot.message_handler(commands=["start", "help"])
def start_command(message):
    user_id = message.from_user.id

    with state_lock:
        busy = user_id in active_jobs

    if busy:
        bot.reply_to(
            message,
            "⏳ لديك طلب قيد المعالجة. انتظر حتى ينتهي."
        )
        return

    text = (
        "مرحباً بك في Media Downloader Bot 🚀\n\n"
        "أرسل رابط فيديو عام من منصة مدعومة، "
        "وسأحاول تنزيله وإرساله إليك.\n\n"
        "📌 قبل البدء، يمكنك زيارة حسابنا على إنستغرام."
    )

    sent = bot.send_message(
        message.chat.id,
        text,
        reply_markup=instagram_keyboard()
    )

    remember_message(user_id, sent)


# =========================================================
# 6. متابعة المستخدم وطلب الإعلان
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "continue_download"
)
def continue_download(call):
    user_id = call.from_user.id

    with state_lock:
        has_pending_url = user_id in pending_urls
        busy = user_id in active_jobs

    if busy:
        bot.answer_callback_query(
            call.id,
            "يوجد طلب قيد المعالجة."
        )
        return

    if not has_pending_url:
        bot.answer_callback_query(
            call.id,
            "أرسل رابط الفيديو أولاً."
        )
        return

    bot.answer_callback_query(
        call.id,
        "تم تسجيل المتابعة."
    )

    # تسجيل الطلب كطلب نشط لمنع تكراره
    with state_lock:
        if user_id in active_jobs:
            return

        active_jobs.add(user_id)

    # إرسال زر فتح الإعلان الخارجي
    try:
        sent = send_tracked_message(
            user_id,
            call.message.chat.id,
            "📢 افتح صفحة الإعلان من الزر أدناه.\n\n"
            "سيبدأ تجهيز الفيديو بعد 10 ثوانٍ من الآن.",
            reply_markup=ad_keyboard()
        )

    except Exception:
        clear_job(user_id)

        bot.send_message(
            call.message.chat.id,
            "❌ تعذر عرض زر الإعلان. حاول مرة أخرى."
        )
        return

    # بدء مؤقت غير ظاهر للمستخدم
    timer = threading.Timer(
        WAIT_SECONDS,
        process_download,
        args=(user_id, call.message.chat.id)
    )

    timer.daemon = True
    timer.start()


# =========================================================
# 7. زر تحميل فيديو آخر
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "next_video"
)
def next_video(call):
    bot.answer_callback_query(
        call.id,
        "أرسل رابط الفيديو التالي."
    )

    send_tracked_message(
        call.from_user.id,
        call.message.chat.id,
        "📎 أرسل رابط الفيديو الجديد للبدء."
    )


# =========================================================
# 8. استقبال روابط الفيديو
# =========================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: not message.text.startswith("/")
)
def receive_video_url(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    video_url = message.text.strip()

    if not valid_http_url(video_url):
        bot.reply_to(
            message,
            "⚠️ أرسل رابطاً صحيحاً يبدأ بـ http:// أو https://"
        )
        return

    with state_lock:
        if user_id in active_jobs:
            bot.reply_to(
                message,
                "⏳ طلبك السابق قيد الانتظار أو التحميل. "
                "انتظر حتى ينتهي."
            )
            return

        if user_id in pending_urls:
            bot.reply_to(
                message,
                "⚠️ لديك رابط محفوظ بالفعل. "
                "اضغط زر المتابعة لإكمال الطلب."
            )
            return

        pending_urls[user_id] = video_url

    try:
        sent = send_tracked_message(
            user_id,
            chat_id,
            "⚠️ لتحميل الفيديو، اضغط زر المتابعة أدناه أولاً.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📢 متابعة لفتح الإعلان",
                            callback_data="continue_download"
                        )
                    ]
                ]
            )
        )

    except Exception:
        clear_job(user_id)
        bot.reply_to(
            message,
            "❌ تعذر إنشاء طلب التحميل. حاول مجدداً."
        )


# =========================================================
# 9. تنزيل الفيديو وإرساله
# =========================================================

def process_download(user_id, chat_id):
    """تنزيل الرابط المحفوظ بعد انتهاء المؤقت."""

    with state_lock:
        video_url = pending_urls.get(user_id)

    if not video_url:
        clear_job(user_id)
        return

    request_id = uuid.uuid4().hex
    output_template = str(
        DOWNLOAD_DIR / f"{user_id}_{request_id}.%(ext)s"
    )

    downloaded_file = None
    status_message = None
    download_succeeded = False

    try:
        status_message = bot.send_message(
            chat_id,
            "⏳ جارٍ تحميل الفيديو، يرجى الانتظار..."
        )

        ydl_opts = {
            "outtmpl": output_template,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "max_filesize": MAX_FILE_SIZE,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "socket_timeout": 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                video_url,
                download=True
            )

            downloaded_file = Path(
                ydl.prepare_filename(info)
            )

        # بعض الصيغ قد تستخدم امتداداً مختلفاً بعد التنزيل
        if not downloaded_file.exists():
            candidates = list(
                DOWNLOAD_DIR.glob(f"{user_id}_{request_id}.*")
            )

            if candidates:
                downloaded_file = candidates[0]

        if not downloaded_file or not downloaded_file.exists():
            raise FileNotFoundError(
                "لم يتم العثور على ملف الفيديو بعد التنزيل."
            )

        file_size = downloaded_file.stat().st_size

        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                "حجم الفيديو أكبر من الحد المسموح به وهو 50 ميغابايت."
            )

        # إرسال الفيديو
        with downloaded_file.open("rb") as video:
            bot.send_video(
                chat_id,
                video,
                supports_streaming=True,
                timeout=120
            )

        download_succeeded = True

        logger.info(
            "نجح التحميل للمستخدم %s",
            user_id
        )

    except Exception as exc:
        logger.exception(
            "فشل التحميل للمستخدم %s",
            user_id
        )

        bot.send_message(
            chat_id,
            "❌ تعذر تحميل الفيديو.\n\n"
            "تأكد من أن الرابط عام ومدعوم، "
            "وأن الفيديو ليس أكبر من 50 ميغابايت.\n\n"
            f"التفاصيل: {str(exc)[:500]}"
        )

    finally:
        # حذف ملف الفيديو المؤقت
        if downloaded_file and downloaded_file.exists():
            try:
                downloaded_file.unlink()
            except OSError:
                logger.warning(
                    "تعذر حذف الملف المؤقت: %s",
                    downloaded_file
                )

        # حذف رسالة الانتظار
        if status_message:
            try:
                bot.delete_message(
                    chat_id,
                    status_message.message_id
                )
            except Exception:
                pass

        # إنهاء حالة الطلب
        clear_job(user_id)

    # حذف رسائل الإعلان السابقة بعد نجاح الإرسال فقط
    if download_succeeded:
        delete_tracked_messages(user_id)

        try:
            bot.send_message(
                chat_id,
                "✅ اكتمل التحميل بنجاح.\n\n"
                "لتحميل فيديو آخر، أرسل رابطه.",
                reply_markup=next_video_keyboard()
            )
        except Exception:
            logger.exception(
                "تعذر إرسال رسالة إكمال التحميل."
            )


# =========================================================
# 10. تشغيل البوت
# =========================================================

if __name__ == "__main__":
    logger.info("Bot is starting...")

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )
        except Exception:
            logger.exception(
                "حدث خطأ في الاتصال بتيليغرام. "
                "ستتم محاولة إعادة التشغيل بعد 5 ثوانٍ."
            )
            time.sleep(5)
            
