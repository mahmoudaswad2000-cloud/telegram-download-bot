import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

# تتبع حالة كل مستخدم بدقة لمنع تجاوز الإعلان
user_ad_status = {}

# دالة لحفظ ومعرفة عدد المستخدمين في ملف نصي محلي
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

# أمر الإحصائيات لمعرفة عدد مستخدمي البوت
@bot.message_handler(commands=['stats'])
def show_stats(message):
    count = get_users_count()
    bot.reply_to(message, f"📊 **إحصائيات البوت:**\n\nعدد المستخدِمين الإجمالي: **{count}** مستخدم.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    save_user(user_id)  # تسجيل المستخدم عند الضغط على start
    user_ad_status[user_id] = False 
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="done_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\nللبدء، يرجى متابعة حسابنا الإجباري على الإنستغرام أولاً ثم الضغط على زر التأكيد أدناه:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "done_insta")
def after_instagram(call):
    user_id = call.from_user.id
    user_ad_status[user_id] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", callback_data="click_ad"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nالآن لتحميل أي فيديو من أي منصة، يجب عليك الضغط على زر الإعلان أدناه أولاً:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "click_ad")
def handle_ad_click(call):
    user_id = call.from_user.id
    user_ad_status[user_id] = True
    bot.answer_callback_query(call.id, url=AD_URL)
    
    bot.send_message(
        call.message.chat.id,
        "✅ شكراً لك! تم تفعيل إذن التحميل. أرسل رابط الفيديو (من يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتحميله فوراً:"
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)  # تسجيل المستخدم عند إرسال أي رابط أو رسالة
    text = message.text.strip()
    
    if text.startswith('http'):
        # التحقق الحاسم: هل ضغط المستخدم على زر الإعلان؟
        if not user_ad_status.get(user_id, False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان أولاً", callback_data="click_ad"))
            
            bot.reply_to(
                message,
                "⚠️ عذراً! لا يمكنك تحميل الفيديو حتى تضغط على زر الإعلان أدناه أولاً:",
                reply_markup=markup
            )
            return

        # إبطال الإذن فوراً لكي يضطر لضغط الإعلان في الفيديو القادم
        user_ad_status[user_id] = False

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

            # إرسال زر الإعلان فقط لتحميل الفيديو القادم
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="click_ad"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه أولاً ثم أرسل الرابط:",
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
            
