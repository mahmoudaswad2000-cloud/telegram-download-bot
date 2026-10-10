import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw?psln=bHVtbTd0NGVkaWh2"
AD_URL = "https://uplcm.com/4/11968073"

# تتبع حالة كل مستخدم لضمان الشروط الحقيقية
user_tracker = {}

def get_user_tracker(user_id):
    if user_id not in user_tracker:
        user_tracker[user_id] = {
            'checked_insta': False,
            'checked_ad': False
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
    tracker['checked_ad'] = False
    
    # الخطوة الأولى: إظهار زر فتح رابط الإنستغرام وزر التأكيد
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
    
    # تسجيل أن المستخدم قام بالمرور من خطوة الإنستغرام
    tracker['checked_insta'] = True
    
    # الانتقال لخطوة الإعلان (التي ستظهر لكل فيديو)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان وفتح التحميل", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان، تفعيل التحميل", callback_data="verify_ad"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لتحميل أي فيديو:\n1️⃣ اضغط على **مشاهدة الإعلان** (سيفتح المتصفح الخارجي فوراً).\n2️⃣ ثم اضغط على زر **تفعيل التحميل** أدناه:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_ad")
def verify_ad(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    if not tracker.get('checked_insta', False):
        bot.answer_callback_query(call.id, text="⚠️ يجب إتمام خطوة الإنستغرام أولاً!", show_alert=True)
        return

    tracker['checked_ad'] = True
    bot.answer_callback_query(call.id, text="✅ تم تفعيل التحميل بنجاح!")
    
    bot.send_message(
        call.message.chat.id,
        "✅ تم التفعيل بنجاح!\n\nأرسل رابط الفيديو الآن (من يوتيوب، إنستغرام، تيك توك، فيسبوك...) وسأقوم بتحميله فوراً:"
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        # التحقق: هل أتم خطوة الإنستغرام والإعلان الحالي؟
        if not tracker.get('checked_insta', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الإنستغرام", url=INSTAGRAM_URL))
            markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verify_insta"))
            bot.reply_to(message, "⚠️ يرجى متابعة حسابنا على الإنستغرام أولاً:", reply_markup=markup)
            return

        if not tracker.get('checked_ad', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان وفتح التحميل", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان، تفعيل التحميل", callback_data="verify_ad"))
            bot.reply_to(message, "⚠️ يرجى مشاهدة الإعلان أولاً ثم الضغط على زر التفعيل:", reply_markup=markup)
            return

        # إبطال حالة الإعلان لإجباره على مشاهدة إعلان جديد للفيديو القادم
        tracker['checked_ad'] = False

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
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان، تفعيل التحميل", callback_data="verify_ad"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان ثم زر التفعيل أدناه:",
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
