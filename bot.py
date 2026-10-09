import os
import time
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

AD_WAIT_SECONDS = 10
user_states = {}

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
    user_states[user_id] = {'authorized': False, 'remaining': 0}
    
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
    if user_id not in user_states:
        user_states[user_id] = {'authorized': False, 'remaining': 0}
    user_states[user_id]['authorized'] = False
    user_states[user_id]['remaining'] = AD_WAIT_SECONDS
    
    # استخدام زر رابط حقيقي (url) ليعمل مباشرة دون أي تعطيل
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", url=AD_URL))
    markup.add(InlineKeyboardButton("⏳ اضغط هنا لبدء عداد الانتظار بعد فتح الإعلان", callback_data="start_timer"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nلتحميل الفيديو:\n1. اضغط على زر **مشاهدة الإعلان** بالأعلى.\n2. اضغط على زر **بدء عداد الانتظار** وانتظر حتى ينتهي لفتح التحميل:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_timer")
def start_timer_callback(call):
    user_id = call.from_user.id
    
    if user_id not in user_states:
        user_states[user_id] = {'authorized': False, 'remaining': AD_WAIT_SECONDS}

    # تشغيل العد التنازلي وتحديث الزر
    while user_states[user_id]['remaining'] > 0:
        rem = user_states[user_id]['remaining']
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان مرة أخرى", url=AD_URL))
        markup.add(InlineKeyboardButton(f"⏳ جاري تحقق مشاهدة الإعلان ({rem} ثوانٍ)...", callback_data="waiting"))
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        except Exception:
            pass
        
        time.sleep(1)
        user_states[user_id]['remaining'] -= 1

    # عند انتهاء العداد بنجاح
    user_states[user_id]['authorized'] = True
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تم التفعيل بنجاح، أرسل الرابط الآن", callback_data="verified"))
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        "✅ تم تأكيد مشاهدة الإعلان بنجاح!\n\nأرسل رابط الفيديو الآن (من يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتحميله فوراً:"
    )

@bot.callback_query_handler(func=lambda call: call.data in ["waiting", "verified"])
def handle_passive_clicks(call):
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    
    if user_id not in user_states:
        user_states[user_id] = {'authorized': False, 'remaining': AD_WAIT_SECONDS}

    if text.startswith('http'):
        if not user_states[user_id].get('authorized', False):
            rem = user_states[user_id].get('remaining', AD_WAIT_SECONDS)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان", url=AD_URL))
            
            bot.reply_to(
                message,
                f"⏳ **تمهل حتى ينتهي العداد!**\nعذراً، لا يمكنك إرسال الرابط الآن. متبقي **{rem} ثوانٍ** لإنهاء مشاهدة الإعلان:",
                reply_markup=markup
            )
            return

        # إبطال الإذن فوراً للمرة القادمة وإعادة ضبط العداد
        user_states[user_id]['authorized'] = False
        user_states[user_id]['remaining'] = AD_WAIT_SECONDS

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
            markup.add(InlineKeyboardButton("⏳ اضغط هنا لبدء عداد التحميل التالي", callback_data="start_timer"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان ثم زر بدء العداد أدناه:",
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
