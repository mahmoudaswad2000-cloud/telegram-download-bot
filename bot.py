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
    
    # إظهار زر واحد فقط للإعلان
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان وفتح التحميل", callback_data="open_ad_hidden_timer"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لتحميل أي فيديو، اضغط على زر الإعلان أدناه لفتحه في المتصفح والانتظار 10 ثوانٍ، ثم أرسل رابط الفيديو مباشرة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def run_hidden_timer(user_id):
    tracker = get_user_tracker(user_id)
    tracker['is_counting'] = True
    tracker['can_download'] = False
    
    # العداد المخفي لمدة 10 ثوانٍ في الخلفية
    time.sleep(AD_WAIT_SECONDS)
    
    tracker['is_counting'] = False
    tracker['can_download'] = True

@bot.callback_query_handler(func=lambda call: call.data == "open_ad_hidden_timer")
def open_ad_hidden_timer(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    tracker['clicked_ad'] = True
    
    # 1. فتح رابط الإعلان فوراً في المتصفح الخارجي
    bot.answer_callback_query(call.id, url=AD_URL)
    
    # 2. تشغيل العداد المخفي في الخلفية
    if not tracker.get('is_counting', False):
        threading.Thread(target=run_hidden_timer, args=(user_id,)).start()
    
    bot.send_message(
        call.message.chat.id,
        "⏳ **تم فتح الإعلان بنجاح!**\nيرجى البقاء في صفحة الإعلان لمدة **10 ثوانٍ**، وبعدها أرسل رابط الفيديو وسأقوم بتحميله فوراً:"
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        # 1. التحقق من شرط الإنستغرام
        if not tracker.get('checked_insta', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", url=INSTAGRAM_URL))
            markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
            bot.reply_to(message, "⚠️ يرجى متابعة حسابنا على الإنستغرام أولاً:", reply_markup=markup)
            return

        # 2. إذا لم يضغط على زر الإعلان نهائياً
        if not tracker.get('clicked_ad', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان وفتح التحميل", callback_data="open_ad_hidden_timer"))
            bot.reply_to(
                message,
                "⚠️ **عذراً! يجب عليك فتح رابط الإعلان أولاً.**\nاضغط على زر الإعلان أدناه وانتظر 10 ثوانٍ ثم أرسل الرابط:",
                reply_markup=markup
            )
            return

        # 3. إذا ضغط على الرابط ولكن العداد المخفي لا يزال يعمل ولم تنتهِ الـ 10 ثوانٍ
        if tracker.get('is_counting', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان مرة أخرى", callback_data="open_ad_hidden_timer"))
            bot.reply_to(
                message,
                "⏳ **الرجاء الانتظار!**\nلم تنتهِ الـ 10 ثوانٍ الخاصة بالإعلان بعد. يرجى الانتظار ثم إرسال الرابط:",
                reply_markup=markup
            )
            return

        # 4. إذا لم يستوفِ التفعيل لأي سبب آخر
        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان وفتح التحميل", callback_data="open_ad_hidden_timer"))
            bot.reply_to(
                message,
                "⚠️ **عذراً!** يجب عليك الضغط على زر الإعلان والانتظار 10 ثوانٍ قبل إرسال الرابط:",
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
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="open_ad_hidden_timer"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه وانتظر 10 ثوانٍ ثم أرسل الرابط مباشرة:",
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
