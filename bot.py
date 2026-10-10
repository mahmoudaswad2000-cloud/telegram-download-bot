import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

# تتبع حالة كل مستخدم لضمان الضغط على الإعلان لكل فيديو
user_ad_status = {}

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
    user_ad_status[user_id] = False 
    
    markup = InlineKeyboardMarkup()
    # زر واحد فقط في بداية التفاعل لصفحة الإنستغرام
    markup.add(InlineKeyboardButton("🔗 تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\nللبدء، يرجى متابعة حسابنا على الإنستغرام عبر الزر أدناه أولاً ثم الضغط على زر الإعلان لفتح التحميل:",
        reply_markup=markup
    )
    
    # إرسال زر الإعلان مباشرة للتحميل
    markup_ad = InlineKeyboardMarkup()
    markup_ad.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", callback_data="click_ad"))
    
    bot.send_message(
        message.chat.id,
        "الآن لتحميل أي فيديو، اضغط على زر الإعلان أدناه للفتح والتفعيل:",
        reply_markup=markup_ad
    )

@bot.callback_query_handler(func=lambda call: call.data == "click_ad")
def handle_ad_click(call):
    user_id = call.from_user.id
    user_ad_status[user_id] = True
    bot.answer_callback_query(call.id, url=AD_URL)
    
    bot.send_message(
        call.message.chat.id,
        "✅ تم تفعيل إذن التحميل بنجاح!\n\nأرسل رابط الفيديو الآن (من يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتحميله فوراً:"
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    
    if text.startswith('http'):
        # التحقق: هل ضغط المستخدم على زر الإعلان؟
        if not user_ad_status.get(user_id, False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان أولاً", callback_data="click_ad"))
            
            bot.reply_to(
                message,
                "⚠️ عذراً! لا يمكنك تحميل الفيديو حتى تضغط على زر الإعلان أدناه أولاً:",
                reply_markup=markup
            )
            return

        # إبطال الإذن فوراً للفيديو القادم
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
            
