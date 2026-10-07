import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8823255880:AAF93L25L5u5EX69Z8vF0xETIQMGV7vZedA"
bot = telebot.TeleBot(TOKEN)

INSTAGRAM_URL = "https://www.instagram.com/mah__asw?stkn=bHVtbTd0NGVkaWh2"
AD_URL = "https://uplcm.com/4/11968073"

# قاعدة بيانات مؤقتة لتتبع حالة المستخدمين
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {'step': 'subscribe_instagram', 'video_url': None}
    return user_states[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    # إعادة ضبط الحالة عند البدء
    user_states[user_id] = {'step': 'subscribe_instagram', 'video_url': None}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 اشترك في إنستغرام أولاً", url=INSTAGRAM_URL))
    markup.add(InlineKeyboardButton("✅ تم الاشتراك، متابعة", callback_data="verified_instagram"))
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت التحميل! 🚀\n\nللبدء واستخدام البوت، يجب عليك أولاً متابعة حسابنا الإجباري على الإنستغرام:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verified_instagram")
def verify_instagram(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    # تحديث الخطوة إلى مشاهدة الإعلان
    state['step'] = 'watch_ad'
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان المطلوب", url=AD_URL))
    markup.add(InlineKeyboardButton("✅ شاهدت الإعلان، فتح التحميل", callback_data="verified_ad"))
    
    bot.edit_message_text(
        "ممتاز! تم تأكيد خطوة الإنستغرام بنجاح ✅\n\nالخطوة الثانية والأخيرة: يرجى مشاهدة الإعلان عبر الرابط أدناه ثم الضغط على زر التأكيد:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verified_ad")
def verify_ad(call):
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    if state['step'] != 'watch_ad':
        bot.answer_callback_query(call.id, "⚠️ يجب عليك إتمام الخطوات بالترتيب!", show_alert=True)
        return
        
    # السماح بالتحميل وإلغاء القيود المؤقتة لهذا الجلسة
    state['step'] = 'ready_to_download'
    
    bot.edit_message_text(
        "رائع جداً! تم استكمال جميع الشروط بنجاح تامن 🎯\n\nالآن، أرسل لي **رابط الفيديو** (من إنستغرام أو أي منصة أخرى) وسأقوم بتحميله وإرساله لك فوراً.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: True)
def handle_incoming_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = get_user_state(user_id)
    
    # إذا أرسل رابطاً وهو لم يكمل الشروط، نمنعه تماماً ونعيده للبداية
    if text.startswith('http'):
        if state['step'] != 'ready_to_download':
            markup = InlineKeyboardMarkup()
            if state['step'] == 'subscribe_instagram':
                markup.add(InlineKeyboardButton("🔗 اشترك في إنستغرام", url=INSTAGRAM_URL))
                markup.add(InlineKeyboardButton("✅ تم الاشتراك", callback_data="verified_instagram"))
                text_msg = "⚠️ عذراً! لا يمكنك تحميل أي فيديو حتى تقوم بمتابعة حسابنا على الإنستغرام أولاً."
            else:
                markup.add(InlineKeyboardButton("📢 مشاهدة الإعلان", url=AD_URL))
                markup.add(InlineKeyboardButton("✅ تم مشاهدة الإعلان", callback_data="verified_ad"))
                text_msg = "⚠️ عذراً! يجب عليك مشاهدة الإعلان أولاً لتفعيل خاصية التحميل."
                
            bot.reply_to(message, text_msg, reply_markup=markup)
            return

        # بدء عملية التحميل الحقيقية
        msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو ومعالجته، يرجى الانتظار...")
        
        try:
            ydl_opts = {
                'outtmpl': 'downloaded_video.mp4',
                'format': 'mp4/best',
                'max_filesize': 50 * 1024 * 1024, # حد أقصى 50 ميجابايت لتوافق تيليغرام
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            if os.path.exists('downloaded_video.mp4'):
                with open('downloaded_video.mp4', 'rb') as vid:
                    bot.send_video(message.chat.id, vid)
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ لم يتم العثور على الفيديو أو حدث خطأ في الرابط.", message.chat.id, msg.message_id)

            # (اختياري) إعادة قفل البوت بطلب الإعلان مجدداً بعد كل تحميل لزيادة الأرباح
            state['step'] = 'watch_ad'
            bot.send_message(
                message.chat.id, 
                "💡 لتحميل فيديو آخر، يرجى مشاهدة الإعلان مجدداً:", 
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("📢 مشاهدة الإعلان", url=AD_URL),
                    InlineKeyboardButton("✅ تم", callback_data="verified_ad")
                )
            )

        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل: تأكد من أن الرابط صحيح وعام.\nالتفاصيل: {str(e)}", message.chat.id, msg.message_id)

        finally:
            if os.path.exists('downloaded_video.mp4'):
                os.remove('downloaded_video.mp4')
    else:
        bot.reply_to(message, "الرجاء إرسال رابط صالح يبدأ بـ http أو إرسال /start للبدء من جديد.")

bot.infinity_polling()
