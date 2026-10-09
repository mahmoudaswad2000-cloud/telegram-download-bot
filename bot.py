import os
import time
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

# رابط الإعلان الخاص بك
AD_URL = "https://uplcm.com/4/11968073"

# قاموس لتتبع حالة كل مستخدم ووقت النقر
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'step': 'watch_ad',
            'click_time': 0
        }
    return user_states[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    state['step'] = 'watch_ad'
    state['click_time'] = time.time()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم / تحقق", callback_data="check_ad"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت التحميل! 🚀\n\nلتحميل الفيديو، يرجى مشاهدة الإعلان أولاً عبر الزر أدناه ثم الضغط على زر (تم / تحقق):",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_ad")
def verify_ad(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    # التأكد من مرور 5 ثوانٍ على الأقل لضمان الدخول إلى الإعلان
    if time.time() - state['click_time'] < 5:
        bot.answer_callback_query(call.id, "⚠️ يرجى الضغط على رابط الإعلان وزيارته أولاً قبل الضغط على تحقق!", show_alert=True)
        return

    # تفعيل صلاحية التحميل
    state['step'] = 'ready_to_download'
    
    bot.edit_message_text(
        "🎯 ممتاز! تم التحقق بنجاح وتفعيل البوت.\n\nالآن أرسل لي رابط الفيديو (من إنستغرام أو أي منصة أخرى) وسأقوم بتحميله وإرساله لك فوراً.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = get_user_state(user_id)
    
    if text.startswith('http'):
        # إذا لم يُكمل شرط الإعلان، يرسل له رسالة الإعلان ويرفض التحميل
        if state['step'] != 'ready_to_download':
            send_welcome(message)
            return

        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو، يرجى الانتظار...")
        try:
            ydl_opts = {
                'outtmpl': 'downloaded_video.mp4',
                'format': 'mp4/best',
                'max_filesize': 50 * 1024 * 1024, # حد أقصى 50 ميجابايت لتناسب تيليغرام
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            if os.path.exists('downloaded_video.mp4'):
                with open('downloaded_video.mp4', 'rb') as vid:
                    bot.send_video(message.chat.id, vid)
                bot.delete_message(message.chat.id, msg.message_id)

            # إعادة إغلاق البوت وإجبار المستخدم على مشاهدة الإعلان من جديد مع الفيديو القادم
            state['step'] = 'watch_ad'
            state['click_time'] = time.time()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 1. مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            markup.add(InlineKeyboardButton("✅ 2. تم / تحقق", callback_data="check_ad"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، يجب عليك مشاهدة الإعلان مجدداً ثم الضغط على زر التحقق:",
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
