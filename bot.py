import os
import time
import threading
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN, threaded=True)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw?psln=bHVtbTd0NGVkaWh2"
AD_URL = "https://uplcm.com/4/11968073"

AD_WAIT_SECONDS = 10
user_tracker = {}

def get_user_tracker(user_id):
    if user_id not in user_tracker:
        user_tracker[user_id] = {
            'clicked_insta_link': False,
            'checked_insta': False,
            'clicked_ad': False,
            'can_download': False,
            'is_counting': False
        }
    return user_tracker[user_id]

def save_user(user_id):
    users = set()
    if os.path.exists('users.txt'):
        with open('users.txt', 'r') as f:
            users = set(line.strip() for line in f if line.strip())
    if str(user_id) not in users:
        with open('users.txt', 'a') as f:
            f.write(f"{user_id}\n")

def get_users_count():
    if not os.path.exists('users.txt'):
        return 0
    with open('users.txt', 'r') as f:
        return len(set(line.strip() for line in f if line.strip()))

@bot.message_handler(commands=['stats'])
def show_stats(message):
    count = get_users_count()
    bot.reply_to(message, f"📊 **إحصائيات البوت:**\n\nعدد المستخدِمين الإجمالي: **{count}** مستخدم.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    save_user(user_id)
    
    tracker = get_user_tracker(user_id)
    tracker['clicked_insta_link'] = False
    tracker['checked_insta'] = False
    tracker['clicked_ad'] = False
    tracker['can_download'] = False
    tracker['is_counting'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 تابعنا على إنستغرام", callback_data="open_insta_link"))
    markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nأهلاً بك، يرجى متابعة حسابنا ثم الضغط على متابعة للبدء:",
        reply_markup=markup
    )

# 1. فتح رابط الإنستغرام وتسجيل الضغطة الفعليه
@bot.callback_query_handler(func=lambda call: call.data == "open_insta_link")
def open_insta_link(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    tracker['clicked_insta_link'] = True
    bot.answer_callback_query(call.id, url=INSTAGRAM_URL)

# 2. التحقق من الضغط الفعلي على رابط الإنستغرام
@bot.callback_query_handler(func=lambda call: call.data == "verify_insta")
def verify_insta(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    if not tracker.get('clicked_insta_link', False):
        bot.answer_callback_query(call.id, text="يرجى الضغط على رابط الإنستغرام أولاً!", show_alert=True)
        return

    tracker['checked_insta'] = True
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 دعم البوت وفتح التحميل", callback_data="open_ad_action"))
    
    bot.edit_message_text(
        "تم التأكيد بنجاح! 🎉\n\nاضغط على الزر أدناه للبدء في استخدام البوت وتحميل الفيديوهات:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def auto_enable_download(chat_id, user_id):
    tracker = get_user_tracker(user_id)
    tracker['is_counting'] = True
    tracker['can_download'] = False
    
    # عداد مخفي بدون إظهاره للمستخدم
    time.sleep(AD_WAIT_SECONDS)
    
    tracker['is_counting'] = False
    tracker['can_download'] = True
    
    try:
        bot.send_message(
            chat_id,
            "✅ **تم التفعيل بنجاح!**\n\nأرسل رابط الفيديو الآن وسأقوم بتحميله فوراً:"
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "open_ad_action")
def open_ad_action(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    tracker = get_user_tracker(user_id)
    
    tracker['clicked_ad'] = True
    
    # التوجيه المباشر لرابط الإعلان
    bot.answer_callback_query(call.id, url=AD_URL)
    
    if not tracker.get('is_counting', False):
        threading.Thread(target=auto_enable_download, args=(chat_id, user_id)).start()
    
    bot.send_message(
        chat_id,
        "جاري التجهيز... يرجى الانتظار لحظات وسيتم فتح إمكانية التحميل لك تلقائياً."
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        # التحقق من الضغط على رابط الإنستغرام
        if not tracker.get('checked_insta', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 تابعنا على إنستغرام", callback_data="open_insta_link"))
            markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
            bot.reply_to(message, "يرجى متابعة حسابنا على الإنستغرام أولاً:", reply_markup=markup)
            return

        # التحقق من الضغط على الإعلان
        if not tracker.get('clicked_ad', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 دعم البوت وفتح التحميل", callback_data="open_ad_action"))
            bot.reply_to(
                message,
                "يرجى الضغط على الزر أدناه أولاً لفتح التحميل:",
                reply_markup=markup
            )
            return

        # في حال أرسل الرابط أثناء فترة التجهيز المخفية
        if tracker.get('is_counting', False):
            bot.reply_to(
                message,
                "⏳ جاري التجهيز، يرجى الانتظار قاطبة وسيكون التحميل جاهزاً..."
            )
            return

        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 دعم البوت وفتح التحميل", callback_data="open_ad_action"))
            bot.reply_to(
                message,
                "يرجى الضغط على الزر أدناه للتمكن من التحميل:",
                reply_markup=markup
            )
            return

        # تصفير حالة الإعلان للفيديو التالي
        tracker['can_download'] = False
        tracker['clicked_ad'] = False

        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو، يرجى الانتظار...")
        try:
            ydl_opts = {
                'outtmpl': 'downloaded_video.mp4',
                'format': 'best/bestvideo+bestaudio/best',
                'max_filesize': 50 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            if os.path.exists('downloaded_video.mp4'):
                with open('downloaded_video.mp4', 'rb') as vid:
                    bot.send_video(message.chat.id, vid)
                bot.delete_message(message.chat.id, msg.message_id)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لتحميل فيديو آخر", callback_data="open_ad_action"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على الزر أدناه ثم أرسل الرابط مباشرة:",
                reply_markup=markup
            )

        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل: تأكد من أن الرابط صالح وعام.\nالتفاصيل: {str(e)}", message.chat.id, msg.message_id)
        finally:
            if os.path.exists('downloaded_video.mp4'):
                os.remove('downloaded_video.mp4')
    else:
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صالح يبدأ بـ http أو إرسال /start للبدء.")

bot.infinity_polling()
            
