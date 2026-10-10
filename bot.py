import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

# قاموس لتتبع النقرات الحقيقية لكل مستخدم
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
    
    # إعادة ضبط تتبع نقرات المستخدم عند البداية
    tracker = get_user_tracker(user_id)
    tracker['clicked_insta'] = False
    tracker['clicked_ad'] = False
    tracker['can_download'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", callback_data="click_insta_link"))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="check_insta_done"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من **يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر** وجميع المنصات.\n\n⚠️ **شرط أساسي:** يجب عليك الضغط على زر الإنستغرام ومتابعتنا أولاً لتفعيل زر التأكيد:",
        reply_markup=markup
    )

# 1. تسجيل الضغطة الحقيقية على رابط الإنستغرام
@bot.callback_query_handler(func=lambda call: call.data == "click_insta_link")
def handle_insta_link_click(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    tracker['clicked_insta'] = True  # تفعيل شرط الإنستغرام
    
    # فتح رابط الإنستغرام فوراً في المتصفح
    bot.answer_callback_query(call.id, url=INSTAGRAM_URL)

# 2. التحقق من الضغط الفعلي على الإنستغرام
@bot.callback_query_handler(func=lambda call: call.data == "check_insta_done")
def check_insta_done(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    if not tracker['clicked_insta']:
        bot.answer_callback_query(
            call.id, 
            text="⚠️ لم تقم بالضغط على زر الإنستغرام بعد! اضغط عليه أولاً ثم اضغط تأكيد.", 
            show_alert=True
        )
        return

    # تم تأكيد الإنستغرام -> الانتقال لخطوة الإعلان
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", callback_data="click_ad_link"))
    markup.add(InlineKeyboardButton("✅ 2. تم مشاهدة الإعلان، فتح التحميل", callback_data="check_ad_done"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nالآن لتفعيل التحميل لكل فيديو:\n1️⃣ اضغط على **زر مشاهدة الإعلان** أدناه.\n2️⃣ بعد فتح الإعلان، اضغط على **زر تأكيد مشاهدة الإعلان**:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# 3. تسجيل الضغطة الحقيقية على الإعلان
@bot.callback_query_handler(func=lambda call: call.data == "click_ad_link")
def handle_ad_link_click(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    tracker['clicked_ad'] = True  # تفعيل شرط الإعلان لهذا الفيديو
    
    # فتح رابط الإعلان فوراً في المتصفح
    bot.answer_callback_query(call.id, url=AD_URL)

# 4. التحقق من الضغط الفعلي على الإعلان
@bot.callback_query_handler(func=lambda call: call.data == "check_ad_done")
def check_ad_done(call):
    user_id = call.from_user.id
    tracker = get_user_tracker(user_id)
    
    if not tracker['clicked_ad']:
        bot.answer_callback_query(
            call.id, 
            text="⚠️ لم تقم بالضغط على زر الإعلان بعد! اضغط عليه أولاً لفتح التحميل.", 
            show_alert=True
        )
        return

    # تم الضغط بنجاح -> إعطاء إذن التحميل للفيديو الحالي فقط
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
        # التحقق الحاسم قبل التحميل
        if not tracker.get('can_download', False):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 1. اضغط هنا لمشاهدة الإعلان", callback_data="click_ad_link"))
            markup.add(InlineKeyboardButton("✅ 2. تم مشاهدة الإعلان، فتح التحميل", callback_data="check_ad_done"))
            
            bot.reply_to(
                message,
                "⚠️ **عذراً! لا يمكنك التحميل حتى تشاهد الإعلان وتؤكده أولاً.**\nيرجى الضغط على زر الإعلان أدناه ثم زر التأكيد:",
                reply_markup=markup
            )
            return

        # إبطال إذن التحميل فوراً للفيديو التالي (إجبار الإعلان لكل فيديو)
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

            # إرسال زر الإعلان والتأكيد للفيديو التالي
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 1. مشاهدة الإعلان لتحميل فيديو آخر", callback_data="click_ad_link"))
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
            
