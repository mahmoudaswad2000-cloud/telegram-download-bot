import os
import time
import threading
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN, threaded=True)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

AD_WAIT_SECONDS = 10
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'authorized': False,
            'remaining': AD_WAIT_SECONDS,
            'is_counting': False
        }
    return user_states[user_id]

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
    
    state = get_user_state(user_id)
    state['authorized'] = False
    state['is_counting'] = False
    state['remaining'] = AD_WAIT_SECONDS
    
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
    state = get_user_state(user_id)
    state['authorized'] = False
    state['is_counting'] = False
    state['remaining'] = AD_WAIT_SECONDS
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", callback_data="single_ad_click"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nاضغط على زر الإعلان أدناه لفتح الإعلان وبدء العداد تلقائياً:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def run_countdown(chat_id, message_id, user_id):
    state = get_user_state(user_id)
    state['is_counting'] = True
    state['remaining'] = AD_WAIT_SECONDS

    while state['remaining'] > 0:
        rem = state['remaining']
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"⏳ يرجى الانتظار في الإعلان ({rem} ثوانٍ)...", callback_data="waiting"))
        try:
            bot.edit_message_reply_markup(
                chat_id,
                message_id,
                reply_markup=markup
            )
        except Exception:
            pass
        
        time.sleep(1)
        state['remaining'] -= 1

    state['authorized'] = True
    state['is_counting'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تم التفعيل بنجاح! أرسل رابط الفيديو الآن", callback_data="verified"))
    try:
        bot.edit_message_reply_markup(
            chat_id,
            message_id,
            reply_markup=markup
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "single_ad_click")
def handle_single_ad_click(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)

    # 1. إعطاء إشعار فتح الإعلان للمستخدم
    bot.answer_callback_query(call.id, url=AD_URL)

    # 2. بدء العداد في خيط منفصل لمنع تجميد السيرفر
    if not state.get('is_counting', False):
        threading.Thread(target=run_countdown, args=(call.message.chat.id, call.message.message_id, user_id)).start()

@bot.callback_query_handler(func=lambda call: call.data in ["waiting", "verified"])
def handle_passive_clicks(call):
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    save_user(user_id)
    text = message.text.strip()
    state = get_user_state(user_id)

    if text.startswith('http'):
        if not state.get('authorized', False):
            rem = state.get('remaining', AD_WAIT_SECONDS)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", callback_data="single_ad_click"))
            
            bot.reply_to(
                message,
                f"⚠️ **تمهل حتى ينتهي العداد!**\nعذراً، لم تنتهِ من مشاهدة الإعلان بعد (متبقي **{rem}** ثوانٍ). اضغط على الزر أعلاه وانتظر انتهاء العداد:",
                reply_markup=markup
            )
            return

        # إعادة ضبط الحالة للمرة القادمة
        state['authorized'] = False
        state['remaining'] = AD_WAIT_SECONDS
        state['is_counting'] = False

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
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="single_ad_click"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه وانتظر العداد:",
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
    
