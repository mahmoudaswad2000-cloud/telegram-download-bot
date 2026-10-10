import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

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
    
    markup = InlineKeyboardMarkup()
    # إبقاء زر تابعنا على إنستغرام فقط دون زر التحقق الوهمي
    markup.add(InlineKeyboardButton("🔗 تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان وبدء التحميل", url=AD_URL))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\nللبدء، يمكنك متابعتنا على الإنستغرام، ثم الضغط على زر الإعلان أدناه لإرسال رابط الفيديو مباشرة:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    
    if text.startswith('http'):
        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو من المنصة المطلوبة، يرجى الانتظار...")
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
            markup.add(InlineKeyboardButton("🔗 تابعنا على إنستغرام", url=INSTAGRAM_URL))
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان ثم أرسل الرابط:",
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
