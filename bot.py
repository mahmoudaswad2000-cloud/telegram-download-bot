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
    tracker['checked_insta'] = False
    tracker['clicked_ad'] = False
    tracker['can_download'] = False
    tracker['is_counting'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من جميع المنصات.\n\n⚠️ **الخطوة الأولى:** اضغط على زر فتح الإنستغرام لمتابعتنا، ثم اضغط على زر **تم الاشتراك، متابعة**:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_insta")
def verify_insta(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    tracker['checked_insta'] = True
    
    # فتح الإعلان في متصفح تيليغرام الداخلي بمجرد الضغط عليه
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان بمتصفح تيليغرام", callback_data="open_app_ad"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لتحميل أي فيديو، اضغط على زر الإعلان أدناه لفتحه في متصفح تيليغرام، وسيتم التفعيل تلقائياً بعد 10 ثوانٍ:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def auto_enable_download(chat_id, user_id):
    tracker = get_user_tracker(user_id)
    tracker['is_counting'] = True
    tracker['can_download'] = False
    
    # العداد لمدة 10 ثوانٍ
    time.sleep(AD_WAIT_SECONDS)
    
    tracker['is_counting'] = False
    tracker['can_download'] = True
    
    try:
        bot.send_message(
            chat_id,
            "✅ **اكتملت الـ 10 ثوانٍ بنجاح!**\nتم فتح إذن التحميل تلقائياً 🎉\n\nأرسل رابط الفيديو الآن وسأقوم بتحميله فوراً:"
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "open_app_ad")
def open_app_ad(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    tracker = get_user_tracker(user_id)
    
    tracker['clicked_ad'] = True
    
    # فتح الرابط في متصفح تيليغرام الداخلي
    bot.answer_callback_query(call.id, url=AD_URL)
    
    # بدء العداد التلقائي بالخلفية
    if not tracker.get('is_counting', False):
        threading.Thread(target=auto_enable_download, args=(chat_id, user_id)).start()
    
    bot.send_message(
        chat_id,
        "📱 **تم فتح الإعلان بمتصفح تيليغرام الداخلي!**\nيرجى الانتظار (10 ثوانٍ) في الإعلان... وسيتم تفعيل التحميل تلقائياً دون أي اضطرار للضغط على زر آخر."
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        # 1. التحقق من الإنستغرام
        if not tracker.get('checked_insta', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", url=INSTAGRAM_URL))
            markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
            bot.reply_to(message, "⚠️ يرجى متابعة حسابنا على الإنستغرام أولاً:", reply_markup=markup)
            return

        # 2. إذا لم يفتح الإعلان
        if not tracker.get('clicked_ad', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان بمتصفح تيليغرام", callback_data="open_app_ad"))
            bot.reply_to(
                message,
                "⚠️ **عذراً! يجب عليك فتح رابط الإعلان أولاً.**\nاضغط على الزر أدناه وانتظر التفعيل التلقائي:",
                reply_markup=markup
            )
            return

        # 3. أثناء الـ 10 ثوانٍ
        if tracker.get('is_counting', False):
            bot.reply_to(
                message,
                "⏳ **يرجى الانتظار!**\nجاري العد التنازلي (10 ثوانٍ) في متصفح تيليغرام، وسنفعل لك التحميل تلقائياً خلال لحظات..."
            )
            return

        # 4. إن لم يكتمل التفعيل
        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان بمتصفح تيليغرام", callback_data="open_app_ad"))
            bot.reply_to(
                message,
                "⚠️ **عذراً!** اضغط على زر الإعلان وانتظر 10 ثوانٍ للتفعيل التلقائي:",
                reply_markup=markup
            )
            return

        # إعادة الضبط للفيديو القادم
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
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="open_app_ad"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان وانتظر 10 ثوانٍ للتفعيل التلقائي ثم أرسل الرابط:",
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
