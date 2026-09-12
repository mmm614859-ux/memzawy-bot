import os
import telebot
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# --- 1. إعدادات البوت والـ API Keys ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "AAH-BJPixbLAG1zCI9kDOKcvTVC1WT1beVg")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LPycXRcm2-qzydtzNHEMteQF-uoSHD_8z98H4UscPzDw")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)


# --- 2. دالة إضافة العلامة المائية الشفافة ---
def add_watermark(image_path, watermark_text="@MemzawyBot"):
    """
    تضيف علامة مائية باللون الأبيض والشفافية الخفيفة 
    في الزاوية السفلية اليسرى للصورة
    """
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        
        # إنشاء طبقة رسم شفافة
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # تحديد حجم الخط بالنسبة لعرض الصورة
        font_size = max(18, int(img.width * 0.045))
        try:
            # استخدام خط افتراضي، أو خط Arial إن وجد
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
            
        # الهوامش والموقع (أسفل يسار الصورة)
        margin = 15
        position = (margin, img.height - font_size - margin)
        
        # رسم النص الشفاف (Alpha = 130 من 255)
        draw.text(position, watermark_text, fill=(255, 255, 255, 130), font=font)
        
        # دمج النص الشفاف على الصورة الأصلية
        watermarked = Image.alpha_composite(img, txt_layer)
        
        output_path = "watermarked_" + os.path.basename(image_path)
        watermarked.convert("RGB").save(output_path, "JPEG")
        return output_path


# --- 3. معالجة أوامر ورسائل البوت ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك في MemzawyBot! 🤖🎨\n\n"
        "أرسل لي أي نص أو فكرة، وسأقوم بتحويلها إلى ميم مضحك فورا!"
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_prompt = message.text
    
    bot.send_message(chat_id, "جاري إنشاء الكوميكس... ⏳")
    
    try:
        # استدعاء Gemini لتوليد الفكرة أو النص
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"اكتب فكرة ميمز قصيرة ومضحكة بناءً على: {user_prompt}")
        
        # مسار صورة القالب (تأكد من وجود صورة template.jpg في مشروعك أو استبدالها بديناميكية)
        template_path = "template.jpg"
        
        if os.path.exists(template_path):
            # 1. إضافة العلامة المائية الشفافة على الصورة
            final_image_path = add_watermark(template_path, "@MemzawyBot")
            
            # 2. إرسال الصورة المائيّة للمستخدم
            with open(final_image_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=response.text)
                
            # 3. حذف الملف المؤقت بعد الإرسال
            if os.path.exists(final_image_path):
                os.remove(final_image_path)
        else:
            # إذا لم تكن الصورة موجودة، يتم إرسال النص فقط
            bot.send_message(chat_id, response.text)
            
    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء معالجة الطلب: {str(e)}")


# --- 4. تشغيل البوت ---
if __name__ == "__main__":
    print("MemzawyBot is running...")
    bot.infinity_polling()

