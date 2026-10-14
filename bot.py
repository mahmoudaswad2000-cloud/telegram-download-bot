import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAHEzXAbs1q1EZZoH2lbWjQEVXPlInHBzno"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw?psln=bHVtbTd0NGVkaWh2"
AD_URL = "https://uplcm.com/4/11968073"

user_ad_status = {}

# دالة حفظ وتتبع المشتركين مع اليوزر نايم والاسم
def save_user(user):
    user_id = user.id
    username = f"@{user.username}" if user.username else "لا يوجد يوزر"
    first_name = user.first_name if user.first_name else ""
    last_name = f" {user.last_name}" if user.last_name else ""
    full_name = f"{first_name}{last_name}".strip() or "لا يوجد اسم"
    
    user_entry = f"{user_id} | {username} | {full_name}"
    
    existing_ids = set()
    if os.path.exists('users.txt'):
        with open('users.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line:
                    existing_ids.add(line.split('|')[0].strip())
                elif line.strip():
                    existing_ids.add(line.strip())

    if str(user_id) not in existing_ids:
        with open('users.txt', 'a', encoding='utf-8') as f:
            f.write(f"{user_entry}\n")

def get_users_info():
    if not os.path.exists('users.txt'):
        return 0, []
    with open('users.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        return len(lines), lines

# أمر الإحصائيات المحدث لتنسيق وإظهار قائمة اليوزرات
@bot.message_handler(commands=['stats'])
def show_stats(message):
    count, users_list = get_users_info()
    
    if count == 0:
        bot.reply_to(message, "📊 **إحصائيات البوت:**\n\nلا يوجد مستخدمين مسجلين حتى الآن.")
        return

    # جلب أحدث 20 مستخدم لمنع تجاوز حد رسائل تيليغرام
    recent_users = users_list[-20:]
    users_formatted = "\n".join([f"👤 `{u}`" for u in recent_users])

    text = (
        f"📊 **إحصائيات البوت:**\n\n"
        f"عدد المستخدِمين الإجمالي: **{count}** مستخدم.\n\n"
        f"📋 **قائمة أحدث المشتركين:**\n"
        f"{users_formatted}"
    )
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    save_user(user)
    user_ad_status[user.id] = False 
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 1. تابعنا على إنستغرام (@mah__asw)", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ 2. تم الاشتراك، متابعة", callback_data="done_insta"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت تحميل الفيديوهات الشامل! 🚀\n\nيدعم البوت التحميل من جميع المنصات.\n\nللبدء، يرجى متابعة حسابنا على الإنستغرام أولاً ثم الضغط على زر التأكيد أدناه:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "done_insta")
def after_instagram(call):
    user_id = call.from_user.id
    user_ad_status[user_id] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", url=AD_URL))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد المتابعة بنجاح ✅\n\nالآن لتحميل أي فيديو، اضغط على زر الإعلان أدناه لفتحه، ثم أرسل رابط الفيديو مباشرة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user = message.from_user
    user_id = user.id
    save_user(user)
    text = message.text.strip()
    
    if text.startswith('http'):
        if not user_ad_status.get(user_id, False):
            user_ad_status[user_id] = True
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان أولاً", url=AD_URL))
            
            bot.reply_to(
                message,
                "⚠️ عذراً! لا يمكنك تحميل الفيديو حتى تضغط على زر الإعلان أدناه أولاً:",
                reply_markup=markup
            )
            return

        user_ad_status[user_id] = False

        file_name = f"video_{user_id}.mp4"
        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو، يرجى الانتظار...")
        try:
            ydl_opts = {
                'outtmpl': file_name,
                'format': 'best/bestvideo+bestaudio/best',
                'max_filesize': 50 * 1024 * 1024,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            if os.path.exists(file_name):
                with open(file_name, 'rb') as vid:
                    bot.send_video(message.chat.id, vid)
                bot.delete_message(message.chat.id, msg.message_id)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", url=AD_URL))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، اضغط على زر الإعلان أدناه أولاً ثم أرسل الرابط:",
                reply_markup=markup
            )

        except Exception as e:
            user_ad_status[user_id] = True
            bot.edit_message_text("❌ متعذر التحميل حالياً من هذا الرابط بسبب قيود المنصة (تأكد من أن الحساب عام وغير خاص).", message.chat.id, msg.message_id)
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)
    else:
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صالح يبدأ بـ http أو إرسال /start للبدء.")

bot.infinity_polling(skip_pending=True)
