import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'step': 'instagram_required'
        }
    return user_states[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    state['step'] = 'instagram_required'
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="done_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت التحميل! 🚀\n\nللبدء لأول مرة، يرجى متابعة حسابنا الإجباري على الإنستغرام ثم الضغط على زر التأكيد أدناه:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "done_insta")
def after_instagram(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    state['step'] = 'ready_to_download'
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان", url=AD_URL))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nالآن لتحميل أي فيديو، شاهد الإعلان عبر الزر أدناه ثم أرسل رابط الفيديو مباشرة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = get_user_state(user_id)
    
    if text.startswith('http'):
        if state['step'] == 'instagram_required':
            send_welcome(message)
            return

        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو، يرجى الانتظار...")
        try:
            ydl_opts = {
                'outtmpl': 'downloaded_video.mp4',
                'format': 'mp4/best',
                'max_filesize': 50 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            if os.path.exists('downloaded_video.mp4'):
                with open('downloaded_video.mp4', 'rb') as vid:
                    bot.send_video(message.chat.id, vid)
                bot.delete_message(message.chat.id, msg.message_id)

            # يرسل زر الإعلان فقط منفرداً دون أي أزرار أخرى
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان", url=AD_URL))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه ثم أرسل رابط الفيديو الجديد مباشرة:",
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
