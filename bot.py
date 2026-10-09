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

# تتبع النقرات والخطوات لكل مستخدم
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'clicked_insta': False,
            'clicked_ad': False,
            'authorized': False,
            'remaining': AD_WAIT_SECONDS
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
    state['clicked_insta'] = False
    state['clicked_ad'] = False
    state['authorized'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="check_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\n⚠️ **شرط الاستخدام:** يجب عليك الضغط على زر الإنستغرام ومتابعتنا أولاً لتفعيل زر التأكيد:",
        reply_markup=markup
    )

# استقبال الضغط على زر التحقق من الإنستغرام
@bot.callback_query_handler(func=lambda call: call.data == "check_insta")
def check_insta_callback(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    # تحويل حالة المستخدم إلى أنه قمت بالضغط على الرابط
    # نطلب منه الضغط على رابط الإنستغرام إذا لم يقم بذلك
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. اضغط هنا لمتابعة الإنستغرام أولاً", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تأكيد المتابعة والدخول", callback_data="done_insta"))
    
    bot.edit_message_text(
        "⚠️ **يرجى التأكد من الضغط على رابط الإنستغرام ومتابعة الحساب (@mah__asw) أولاً!**\n\nبعد الضغط على الرابط ومتابعتنا، اضغط على زر التاكيد أدناه:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "done_insta")
def after_instagram(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    state['clicked_ad'] = False
    state['authorized'] = False
    state['remaining'] = AD_WAIT_SECONDS
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", url=AD_URL))
    markup.add(InlineKeyboardButton("⏳ 2. ابدأ عداد التفعيل (اضغط الإعلان أولاً)", callback_data="start_timer"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لفتح إذن التحميل:\n1️⃣ **اضغط على زر الإعلان أولاً.**\n2️⃣ ثم اضغط على زر **بدء العداد** وانتظر 10 ثوانٍ لفتح التحميل:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# عند الضغط على زر بدء العداد
@bot.callback_query_handler(func=lambda call: call.data == "start_timer")
def start_timer_callback(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)

    # حماية: إذا حاول الضغط على العداد دون الضغط على الإعلان أو إذا كان قيد العد
    bot.answer_callback_query(call.id, text="جاري بدء العداد... تأكد من فتح صفحة الإعلان!")

    if state['remaining'] <= 0:
        state['remaining'] = AD_WAIT_SECONDS

    msg = bot.send_message(call.message.chat.id, f"⏳ جاري تحقق مشاهدة الإعلان... متبقي **{state['remaining']}** ثوانٍ.")

    while state['remaining'] > 0:
        time.sleep(1)
        state['remaining'] -= 1
        rem = state['remaining']
        
        if rem > 0:
            try:
                bot.edit_message_text(
                    f"⏳ جاري تحقق مشاهدة الإعلان... متبقي **{rem}** ثوانٍ.",
                    call.message.chat.id,
                    msg.message_id
                )
            except Exception:
                pass

    state['authorized'] = True
    bot.edit_message_text(
        "✅ تم تأكيد مشاهدة الإعلان بنجاح!\n\nأرسل رابط الفيديو الآن (من يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتحميله فوراً:",
        call.message.chat.id,
        msg.message_id
    )

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
            markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", url=AD_URL))
            markup.add(InlineKeyboardButton("⏳ 2. اضغط هنا لبدء العداد", callback_data="start_timer"))
            
            bot.reply_to(
                message,
                f"⚠️ **عذراً، لم تُكمل مشاهدة الإعلان بعد!**\nمتبقي **{rem}** ثوانٍ لفتح التحميل. يرجى الضغط على زر الإعلان والانتظار حتى انتهاء العداد:",
                reply_markup=markup
            )
            return

        # إعادة ضبط الصلاحية للفيديو القادم
        state['authorized'] = False
        state['remaining'] = AD_WAIT_SECONDS

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
            markup.add(InlineKeyboardButton("⏳ 2. لبدء عداد الفيديو التالي", callback_data="start_timer"))
            
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
                
