import os
import time
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

# قاموس لتتبع حالة كل مستخدم
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'step': 'subscribe_instagram'
        }
    return user_states[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    state['step'] = 'subscribe_instagram'
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="verified_instagram"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت التحميل! 🚀\n\nللبدء، يرجى متابعة حسابنا الإجباري على الإنستغرام (`@mah__asw`) ثم الضغط على زر التأكيد:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verified_instagram")
def verify_instagram(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    # الانتقال لخطوة مشاهدة الإعلان
    state['step'] = 'watch_ad'
    
    markup = InlineKeyboardMarkup()
    # بمجرد ضغط المستخدم على هذا الزر (رابط الإعلان)، سيتم فتح الإعلان، وبما أنه زر رابط، سنقوم بتوفير زر انتقال مباشر لفتح التحميل أو نجعله ينتقل للخطوة التالية
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان وفتح التحميل", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان (تفعيل التحميل)", callback_data="ready_download"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد إنستغرام ✅\n\nالخطوة الأخيرة: اضغط على رابط الإعلان أدناه، وبعدها اضغط على زر تفعيل التح:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "ready_download")
def activate_download(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    state['step'] = 'ready_to_download'
    
    bot.edit_message_text(
        "🎯 رائع جداً! تم تفعيل البوت بنجاح.\n\nالآن أرسل لي رابط الفيديو (من إنستغرام أو أي منصة) وسأقوم بتحميله وإرساله لك فوراً.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = get_user_state(user_id)
    
    if text.startswith('http'):
        if state['step'] != 'ready_to_download':
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

            # إعادة قفل البوت وإلزام الإعلان لتحميل فيديو جديد
            state['step'] = 'watch_ad'
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان وتفعيل التحميل", callback_data="ready_download"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، يرجى مشاهدة الإعلان مجدداً ثم تفعيل التحميل:",
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
