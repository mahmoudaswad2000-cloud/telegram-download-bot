import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

# الروابط المحدثة
INSTAGRAM_URL = "https://www.instagram.com/mah__asw?psln=bHVtbTd0NGVkaWh2"
AD_URL = "https://uplcm.com/4/11968073"

# قاموس لتتبع حالة كل مستخدم
user_tracker = {}

def get_user_tracker(user_id):
    if user_id not in user_tracker:
        user_tracker[user_id] = {
            'clicked_insta': False,
            'clicked_ad': False,
            'can_download': False
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
    tracker['clicked_insta'] = False
    tracker['clicked_ad'] = False
    tracker['can_download'] = False
    
    markup = InlineKeyboardMarkup()
    # استخدام url المباشر يضمن فتح الرابط بدون أي مشاكل
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="check_insta_done"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\n⚠️ **شرط أساسي:** يجب عليك الضغط على زر الإنستغرام ومتابعتنا أولاً ثم الضغط على زر التأكيد:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_insta_done")
def check_insta_done(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    # تسجيل التأكيد
    tracker['clicked_insta'] = True

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم مشاهدة الإعلان، فتح التحميل", callback_data="check_ad_done"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nالآن لتفعيل التحميل لكل فيديو:\n1️⃣ اضغط على **زر مشاهدة الإعلان** أدناه.\n2️⃣ بعد فتح الإعلان، اضغط على **زر تأكيد مشاهدة الإعلان**:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_ad_done")
def check_ad_done(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    tracker['clicked_ad'] = True
    tracker['can_download'] = True
    
    bot.answer_callback_query(call.id, text="✅ تم تفعيل التحميل بنجاح!")
    
    bot.send_message(
        call.message.chat.id,
        "✅ تم تأكيد الإعلان وتفعيل إذن التحميل!\n\nأرسل رابط الفيديو الآن (من يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتحميله فوراً:"
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    tracker = get_user_tracker(user_id)

    if text.startswith('http'):
        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ 2. تم مشاهدة الإعلان، فتح التحميل", callback_data="check_ad_done"))
            
            bot.reply_to(
                message,
                "⚠️ **عذراً! لا يمكنك التحميل حتى تشاهد الإعلان وتؤكده أولاً.**\nيرجى الضغط على زر الإعلان أدناه ثم زر التأكيد:",
                reply_markup=markup
            )
            return

        # إبطال إذن التحميل فوراً للفيديو التالي
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
            markup.add(InlineKeyboardButton("📢 1. مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ 2. تأكيد مشاهدة الإعلان للتفعيل", callback_data="check_ad_done"))
            
            bot.send_message(
                message.chat.id,
                "💡 **لتحميل فيديو آخر:** يجب عليك الضغط على زر الإعلان أدناه أولاً ثم اضغط على زر التأكيد:",
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
