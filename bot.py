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
    tracker['can_download'] = False
    tracker['is_counting'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", callback_data="open_insta"))
    markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من جميع المنصات.\n\nيرجى متابعة حسابنا عبر الزر أدناه ثم الضغط على متابعة:",
        reply_markup=markup
    )

# فتح رابط الإنستغرام وتسجيل الضغطة الفعليه
@bot.callback_query_handler(func=lambda call: call.data == "open_insta")
def open_insta(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    tracker['clicked_insta_link'] = True
    bot.answer_callback_query(call.id, url=INSTAGRAM_URL)

# التحقق من الضغط الفعلي على الإنستغرام
@bot.callback_query_handler(func=lambda call: call.data == "verify_insta")
def verify_insta(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    tracker = get_user_tracker(user_id)
    
    # إذا لم يضغط على رابط الإنستغرام يتم الرفض وإعادة الرسالة
    if not tracker.get('clicked_insta_link', False):
        bot.answer_callback_query(call.id, text="⚠️ يجب عليك الضغط على رابط الإنستغرام أولاً!", show_alert=True)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", callback_data="open_insta"))
        markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
        
        bot.edit_message_text(
            "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من جميع المنصات.\n\nيرجى متابعة حسابنا عبر الزر أدناه ثم الضغط على متابعة:",
            chat_id,
            call.message.message_id,
            reply_markup=markup
        )
        return

    tracker['checked_insta'] = True
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان", callback_data="open_ad"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لتحميل أي فيديو، اضغط على زر الإعلان أدناه:",
        chat_id,
        call.message.message_id,
        reply_markup=markup
    )

def auto_enable_download(chat_id, user_id):
    tracker = get_user_tracker(user_id)
    tracker['is_counting'] = True
    tracker['can_download'] = False
    
    time.sleep(AD_WAIT_SECONDS)
    
    tracker['is_counting'] = False
    tracker['can_download'] = True
    
    try:
        bot.send_message(
            chat_id,
            "✅ تم التفعيل بنجاح!\n\nأرسل رابط الفيديو الآن وسأقوم بتحميله فوراً:"
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "open_ad")
def open_ad(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    tracker = get_user_tracker(user_id)
    
    bot.answer_callback_query(call.id, url=AD_URL)
    
    if not tracker.get('is_counting', False):
        threading.Thread(target=auto_enable_download, args=(chat_id, user_id)).start()

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        if not tracker.get('checked_insta', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", callback_data="open_insta"))
            markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
            bot.reply_to(message, "يرجى متابعة حسابنا على الإنستغرام أولاً:", reply_markup=markup)
            return

        if tracker.get('is_counting', False):
            bot.reply_to(message, "⏳ جاري التجهيز، يرجى الانتظار لحظات...")
            return

        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان", callback_data="open_ad"))
            bot.reply_to(
                message,
                "يرجى الضغط على زر الإعلان أدناه أولاً:",
                reply_markup=markup
            )
            return

        tracker['can_download'] = False

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
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="open_ad"))

            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه ثم أرسل الرابط:",
                reply_markup=markup
            )

        except Exception as e:
            tracker['can_download'] = True
            bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل: تأكد من أن الرابط صالح وعام.\nالتفاصيل: {str(e)}", message.chat.id, msg.message_id)
        finally:
            if os.path.exists('downloaded_video.mp4'):
                os.remove('downloaded_video.mp4')
    else:
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صالح يبدأ بـ http أو إرسال /start للبدء.")

bot.infinity_polling()
        
