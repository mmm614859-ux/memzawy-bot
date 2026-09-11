"""
MemzawyBot (@MemzawyBot) - AI Meme Generator Telegram Bot
==========================================================
Features:
  1. Mandatory channel subscription check
  2. Arabic / English language menu
  3. AI meme caption generator (Gemini gemini-1.5-flash)
  4. Manual image editor (burn custom text onto image with Pillow)
  5. Sticker export (512x512 PNG)

Libraries: pyTelegramBotAPI (telebot), google-generativeai, Pillow
"""

import os
import io
import logging

import telebot
from telebot import types

from PIL import Image, ImageDraw, ImageFont

import google.generativeai as genai

# =========================================================
# CONFIGURATION - Replace with your real values
# =========================================================
BOT_TOKEN = "8960745150:AAH-BJPixbLAG1zCI9kDOKcvTVC1WT1beVg"
GEMINI_API_KEY = "AQ.Ab8RN6LPycXRcm2-qzydtzNHEMteQF-uoSHD_8z98H4UscPzDw"
CHANNEL_USERNAME = "@M98985"   # Mandatory subscription channel

# Optional: path to a .ttf font file bundled with your project.
# If not found, Pillow's default bitmap font is used as a fallback.
FONT_PATH = "impact.ttf"

# =========================================================
# INIT
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemzawyBot")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# In-memory per-user state (use a DB for production/multi-instance deploys)
# Structure: user_states[user_id] = {"lang": "en"/"ar", "mode": "...", "image": bytes, ...}
user_states = {}


def get_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {"lang": "en", "mode": None, "image_bytes": None}
    return user_states[user_id]


# =========================================================
# TEXT / TRANSLATIONS
# =========================================================
TEXTS = {
    "en": {
        "join_prompt": "🚫 You must join our channel to use this bot.",
        "join_button": "📢 Join Channel",
        "check_button": "✅ I Joined",
        "still_not_joined": "❗ You haven't joined the channel yet. Please join then press 'I Joined'.",
        "welcome": (
            "🎉 Welcome to <b>MemzawyBot</b>!\n\n"
            "Choose your language / اختر لغتك:"
        ),
        "main_menu_title": "🏠 Main Menu — choose an option:",
        "btn_ai_caption": "🤖 AI Caption Generator",
        "btn_manual_edit": "✍️ Manual Meme Editor",
        "btn_language": "🌐 Change Language",
        "btn_back": "⬅️ Back",
        "ask_topic": "Send me a topic, some text, or an image and I'll generate 3 funny meme captions!",
        "generating": "🤔 Generating witty captions, please wait...",
        "gemini_error": "⚠️ Something went wrong generating captions. Please try again.",
        "ask_image_manual": "📸 Send me the image you want to turn into a meme.",
        "ask_text_manual": "✏️ Now send me the text you want to burn onto the image.",
        "ask_position": "📍 Choose text position:",
        "pos_top": "⬆️ Top",
        "pos_bottom": "⬇️ Bottom",
        "pos_center": "⏺ Center",
        "meme_ready": "✅ Here's your meme!",
        "ask_sticker": "Do you want this as a Telegram Sticker (512x512 PNG)?",
        "yes": "✅ Yes, make sticker",
        "no": "❌ No, just image",
        "sticker_ready": "🖼️ Here's your sticker-ready PNG (512x512). Send it to @Stickers to add it to a pack!",
        "lang_set": "✅ Language set to English.",
        "send_image_first": "Please send an image first.",
        "no_active_edit": "Please start with /start and choose Manual Meme Editor first.",
    },
    "ar": {
        "join_prompt": "🚫 يجب عليك الاشتراك في قناتنا لاستخدام هذا البوت.",
        "join_button": "📢 اشترك في القناة",
        "check_button": "✅ لقد اشتركت",
        "still_not_joined": "❗ لم تشترك في القناة بعد. اشترك ثم اضغط 'لقد اشتركت'.",
        "welcome": (
            "🎉 مرحبًا بك في <b>MemzawyBot</b>!\n\n"
            "اختر لغتك / Choose your language:"
        ),
        "main_menu_title": "🏠 القائمة الرئيسية — اختر خيارًا:",
        "btn_ai_caption": "🤖 مولّد تعليقات بالذكاء الاصطناعي",
        "btn_manual_edit": "✍️ محرر ميمز يدوي",
        "btn_language": "🌐 تغيير اللغة",
        "btn_back": "⬅️ رجوع",
        "ask_topic": "أرسل لي موضوعًا أو نصًا أو صورة وسأقوم بإنشاء 3 تعليقات ميمز مضحكة!",
        "generating": "🤔 جاري إنشاء تعليقات مضحكة، انتظر من فضلك...",
        "gemini_error": "⚠️ حدث خطأ أثناء إنشاء التعليقات. حاول مرة أخرى.",
        "ask_image_manual": "📸 أرسل لي الصورة التي تريد تحويلها إلى ميم.",
        "ask_text_manual": "✏️ الآن أرسل لي النص الذي تريد كتابته على الصورة.",
        "ask_position": "📍 اختر موضع النص:",
        "pos_top": "⬆️ أعلى",
        "pos_bottom": "⬇️ أسفل",
        "pos_center": "⏺ المنتصف",
        "meme_ready": "✅ هذا هو الميم الخاص بك!",
        "ask_sticker": "هل تريد تحويل هذا إلى ملصق تيليجرام (512x512 PNG)؟",
        "yes": "✅ نعم، حوّله لملصق",
        "no": "❌ لا، فقط الصورة",
        "sticker_ready": "🖼️ هذه هي صورتك الجاهزة كملصق (512x512). أرسلها إلى @Stickers لإضافتها لحزمة ملصقات!",
        "lang_set": "✅ تم تعيين اللغة إلى العربية.",
        "send_image_first": "من فضلك أرسل صورة أولاً.",
        "no_active_edit": "من فضلك ابدأ بـ /start واختر محرر الميمز اليدوي أولاً.",
    },
}


def t(user_id, key):
    lang = get_state(user_id).get("lang", "en")
    return TEXTS[lang][key]


# =========================================================
# CHANNEL SUBSCRIPTION CHECK
# =========================================================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning(f"Subscription check failed for {user_id}: {e}")
        return False


def send_subscription_prompt(chat_id, user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            t(user_id, "join_button"),
            url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}",
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            t(user_id, "check_button"), callback_data="check_sub"
        )
    )
    bot.send_message(chat_id, t(user_id, "join_prompt"), reply_markup=markup)


# =========================================================
# MENUS
# =========================================================
def language_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
    )
    return markup


def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_ai_caption"), callback_data="mode_ai"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_manual_edit"), callback_data="mode_manual"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_language"), callback_data="mode_lang"))
    return markup


def position_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(t(user_id, "pos_top"), callback_data="pos_top"),
        types.InlineKeyboardButton(t(user_id, "pos_center"), callback_data="pos_center"),
        types.InlineKeyboardButton(t(user_id, "pos_bottom"), callback_data="pos_bottom"),
    )
    return markup


def sticker_choice_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(t(user_id, "yes"), callback_data="sticker_yes"),
        types.InlineKeyboardButton(t(user_id, "no"), callback_data="sticker_no"),
    )
    return markup


# =========================================================
# GATE DECORATOR - require channel subscription
# =========================================================
def require_subscription(func):
    def wrapper(message_or_call):
        if isinstance(message_or_call, types.CallbackQuery):
            user_id = message_or_call.from_user.id
            chat_id = message_or_call.message.chat.id
        else:
            user_id = message_or_call.from_user.id
            chat_id = message_or_call.chat.id

        if not is_subscribed(user_id):
            send_subscription_prompt(chat_id, user_id)
            return
        return func(message_or_call)

    return wrapper


# =========================================================
# COMMAND: /start
# =========================================================
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    get_state(user_id)  # ensure state exists

    if not is_subscribed(user_id):
        send_subscription_prompt(chat_id, user_id)
        return

    bot.send_message(chat_id, t(user_id, "welcome"), reply_markup=language_menu())


# =========================================================
# CALLBACK HANDLER
# =========================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    state = get_state(user_id)

    # --- Subscription re-check button ---
    if data == "check_sub":
        if is_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            bot.send_message(chat_id, t(user_id, "welcome"), reply_markup=language_menu())
        else:
            bot.answer_callback_query(call.id, t(user_id, "still_not_joined"), show_alert=True)
        return

    # Gate everything else behind subscription
    if not is_subscribed(user_id):
        bot.answer_callback_query(call.id)
        send_subscription_prompt(chat_id, user_id)
        return

    # --- Language selection ---
    if data == "lang_en":
        state["lang"] = "en"
        bot.answer_callback_query(call.id, t(user_id, "lang_set"))
        bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))
        return

    if data == "lang_ar":
        state["lang"] = "ar"
        bot.answer_callback_query(call.id, t(user_id, "lang_set"))
        bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))
        return

    # --- Main menu options ---
    if data == "mode_ai":
        state["mode"] = "ai"
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, t(user_id, "ask_topic"))
        return

    if data == "mode_manual":
        state["mode"] = "manual_wait_image"
        state["image_bytes"] = None
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, t(user_id, "ask_image_manual"))
        return

    if data == "mode_lang":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, t(user_id, "welcome"), reply_markup=language_menu())
        return

    # --- Text position chosen for manual editor ---
    if data in ("pos_top", "pos_center", "pos_bottom"):
        bot.answer_callback_query(call.id)
        position = data.replace("pos_", "")
        if not state.get("image_bytes") or not state.get("pending_text"):
            bot.send_message(chat_id, t(user_id, "no_active_edit"))
            return
        meme_bytes = burn_text_on_image(
            state["image_bytes"], state["pending_text"], position
        )
        state["last_meme_bytes"] = meme_bytes
        bot.send_photo(chat_id, meme_bytes, caption=t(user_id, "meme_ready"))
        bot.send_message(chat_id, t(user_id, "ask_sticker"), reply_markup=sticker_choice_menu(user_id))
        return

    # --- Sticker export choice ---
    if data == "sticker_yes":
        bot.answer_callback_query(call.id)
        meme_bytes = state.get("last_meme_bytes")
        if not meme_bytes:
            bot.send_message(chat_id, t(user_id, "no_active_edit"))
            return
        sticker_bytes = convert_to_sticker(meme_bytes)
        bot.send_document(
            chat_id,
            ("meme_sticker.png", sticker_bytes),
            caption=t(user_id, "sticker_ready"),
        )
        return

    if data == "sticker_no":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))
        return


# =========================================================
# GEMINI: AI CAPTION GENERATOR
# =========================================================
def generate_captions(topic_text, lang="en"):
    if lang == "ar":
        prompt = (
            "أنت كاتب كوميدي متخصص في الميمز. "
            f"اكتب 3 تعليقات ميمز قصيرة ومضحكة جدًا وذكية عن الموضوع التالي: '{topic_text}'. "
            "كل تعليق يجب أن يكون سطرًا واحدًا فقط، ورقّم التعليقات 1، 2، 3."
        )
    else:
        prompt = (
            "You are a witty meme caption writer. "
            f"Write 3 short, funny, clever meme captions about: '{topic_text}'. "
            "Each caption should be one line only. Number them 1, 2, 3."
        )

    response = gemini_model.generate_content(prompt)
    return response.text.strip()


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("mode") == "ai", content_types=["text"])
@require_subscription
def handle_ai_topic_text(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    lang = get_state(user_id).get("lang", "en")

    bot.send_message(chat_id, t(user_id, "generating"))
    try:
        captions = generate_captions(message.text, lang=lang)
        bot.send_message(chat_id, f"🎭 <b>Captions:</b>\n\n{captions}")
    except Exception as e:
        logger.exception("Gemini caption generation failed")
        bot.send_message(chat_id, t(user_id, "gemini_error"))

    bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("mode") == "ai", content_types=["photo"])
@require_subscription
def handle_ai_topic_image(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    lang = get_state(user_id).get("lang", "en")

    caption_hint = message.caption if message.caption else (
        "a random relatable meme situation" if lang == "en" else "موقف ميمز عشوائي ومضحك"
    )

    bot.send_message(chat_id, t(user_id, "generating"))
    try:
        # Gemini text-only fallback: use caption/hint since gemini-1.5-flash
        # vision calls require the image bytes to be sent as inline data.
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        image_part = {"mime_type": "image/jpeg", "data": downloaded}
        if lang == "ar":
            prompt = (
                "أنت كاتب كوميدي متخصص في الميمز. انظر إلى هذه الصورة واكتب 3 تعليقات "
                "ميمز قصيرة ومضحكة جدًا تناسبها. رقّم التعليقات 1، 2، 3."
            )
        else:
            prompt = (
                "You are a witty meme caption writer. Look at this image and write 3 "
                "short, funny meme captions that fit it. Number them 1, 2, 3."
            )

        response = gemini_model.generate_content([prompt, image_part])
        bot.send_message(chat_id, f"🎭 <b>Captions:</b>\n\n{response.text.strip()}")
    except Exception as e:
        logger.exception("Gemini image caption generation failed")
        bot.send_message(chat_id, t(user_id, "gemini_error"))

    bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))


# =========================================================
# MANUAL MEME EDITOR (Pillow)
# =========================================================
@bot.message_handler(
    func=lambda m: get_state(m.from_user.id).get("mode") == "manual_wait_image",
    content_types=["photo"],
)
@require_subscription
def handle_manual_image(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = get_state(user_id)

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded = bot.download_file(file_info.file_path)

    state["image_bytes"] = downloaded
    state["mode"] = "manual_wait_text"

    bot.send_message(chat_id, t(user_id, "ask_text_manual"))


@bot.message_handler(
    func=lambda m: get_state(m.from_user.id).get("mode") == "manual_wait_text",
    content_types=["text"],
)
@require_subscription
def handle_manual_text(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = get_state(user_id)

    if not state.get("image_bytes"):
        bot.send_message(chat_id, t(user_id, "send_image_first"))
        state["mode"] = "manual_wait_image"
        return

    state["pending_text"] = message.text
    state["mode"] = "manual_wait_position"

    bot.send_message(chat_id, t(user_id, "ask_position"), reply_markup=position_menu(user_id))


def get_font(font_size):
    """Load a TTF font if available, otherwise fall back to Pillow's default font."""
    try:
        if os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, font_size)
        return ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except Exception:
        return ImageFont.load_default()


def burn_text_on_image(image_bytes, text, position="bottom"):
    """
    Burns the given text onto the image using Pillow.
    Automatically scales font size based on image width and wraps long text.
    position: "top" | "center" | "bottom"
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)

    img_w, img_h = image.size

    # Dynamic font sizing: ~ 8% of image width, clamped to reasonable bounds
    font_size = max(20, min(int(img_w * 0.08), 90))
    font = get_font(font_size)

    # Simple word-wrap based on estimated character width
    max_width = img_w * 0.9
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Calculate total text block height
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_text_height = sum(line_heights) + (len(lines) - 1) * 10

    # Determine starting Y based on position
    padding = int(img_h * 0.04)
    if position == "top":
        y = padding
    elif position == "center":
        y = (img_h - total_text_height) // 2
    else:  # bottom
        y = img_h - total_text_height - padding

    # Draw each line, centered horizontally, with a black outline (classic meme style)
    outline_range = max(2, font_size // 20)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (img_w - line_w) // 2

        for dx in range(-outline_range, outline_range + 1):
            for dy in range(-outline_range, outline_range + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill="black")
        draw.text((x, y), line, font=font, fill="white")

        y += line_h + 10

    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


# =========================================================
# STICKER CONVERTER (512x512 PNG, Telegram sticker requirements)
# =========================================================
def convert_to_sticker(image_bytes_io):
    """
    Resizes/pads the image to fit Telegram's sticker requirement:
    - PNG format
    - At least one side must be exactly 512px, the other <= 512px
    We produce a clean 512x512 canvas with the image centered (transparent padding).
    """
    image_bytes_io.seek(0)
    image = Image.open(image_bytes_io).convert("RGBA")

    target_size = 512
    image.thumbnail((target_size, target_size), Image.LANCZOS)

    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    paste_x = (target_size - image.width) // 2
    paste_y = (target_size - image.height) // 2
    canvas.paste(image, (paste_x, paste_y), image)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output


# =========================================================
# FALLBACK HANDLER
# =========================================================
@bot.message_handler(func=lambda m: True, content_types=["text", "photo"])
def fallback_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_subscribed(user_id):
        send_subscription_prompt(chat_id, user_id)
        return

    bot.send_message(chat_id, t(user_id, "main_menu_title"), reply_markup=main_menu(user_id))


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    logger.info("MemzawyBot is starting...")
    bot.infinity_polling(skip_pending=True)
