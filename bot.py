import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw"
AD_URL = "https://uplcm.com/4/11968073"

# تتبع حالات المستخدمين
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'step': 'instagram_required',
            'has_clicked_ad': False
        }
    return user_states[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    state['step'] = 'instagram_required'
    state['has_clicked_ad'] = False
    
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
    state['has_clicked_ad'] = False
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان لفتح التحميل", callback_data="open_ad_link"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد الإنستغرام بنجاح ✅\n\nالان يلزمك الضغط على زر الإعلان أدناه أولاً لفتح صلاحية التحميل:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "open_ad_link")
def handle_ad_click(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    # تسجل رسمياً أن المستخدم ضغط على الزر
    state['has_clicked_ad'] = True
    
    # فتح رابط الإعلان للمستخدم تلقائياً عبر المتصفح
    bot.answer_callback_query(call.id, url=AD_URL)
    
    bot.send_message(
        call.message.chat.id,
        "✅ تم فتح الإعلان وتفعيل صلاحية التحميل!\n\nأرسل رابط الفيديو الآن وسأقوم بتحميله فوراً."
    )

@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = get_user_state(user_id)
    
    if text.startswith('http'):
        # 1. إذا لم يُكمل شرط الإنستغرام
        if state['step'] == 'instagram_required':
            send_welcome(message)
            return

        # 2. إذا لم يضغط على زر مشاهدة الإعلان
        if not state['has_clicked_ad']:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اضغط هنا لمشاهدة الإعلان أولاً", callback_data="open_ad_link"))
            
            bot.reply_to(
                message,
                "⚠️ عذراً! لا يمكنك التحميل حتى تضغط على زر الإعلان أدناه أولاً:",
                reply_markup=markup
            )
            return

        # 3. عند تحقق الشرط: جاري التحميل
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

            # إعادة قفل التحميل فوراً للفيديو القادم
            state['has_clicked_ad'] = False
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان لتحميل فيديو آخر", callback_data="open_ad_link"))
            
            bot.send_message(
                message.chat.id,
                "💡 لتحميل فيديو آخر، يجب الضغط على زر الإعلان أدناه أولاً ثم إرسال الرابط:",
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
