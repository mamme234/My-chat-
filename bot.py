import logging
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, GPT_MODEL

# Setup
openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 **Worksheet Answer Bot**\n\n"
        "Send me:\n"
        "• A question as text\n"
        "• A photo of a worksheet or exam\n"
        "• An image file\n\n"
        "I'll reply with **only the answer** - no explanations.\n\n"
        "Made with GPT-4o (reads images directly)",
        parse_mode="Markdown"
    )

async def get_answer_from_text(question: str) -> str:
    """Call GPT to answer directly (no explanations)"""
    try:
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are an answer bot. Respond with ONLY the final answer. No explanations, no extra text, no 'Answer:' prefix. Just the answer."},
                {"role": "user", "content": question}
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def get_answer_from_image(image_url: str, question_hint: str = None) -> str:
    """Call GPT-4o to read image and answer directly"""
    try:
        user_content = [
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
        
        if question_hint:
            user_content.append({"type": "text", "text": question_hint})
        else:
            user_content.append({"type": "text", "text": "Answer the question in this image. Provide only the final answer, no explanation."})
        
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You read text from images and answer questions directly. Respond with ONLY the answer. No explanations, no extra text."},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_chat_action(action="typing")
    answer = await get_answer_from_text(question)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the highest quality photo
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_url = file.file_path
    
    await update.message.reply_text("📖 Reading image...")
    await update.message.reply_chat_action(action="typing")
    
    # Check if user added a caption (extra question text)
    caption = update.message.caption
    answer = await get_answer_from_image(file_url, caption)
    await update.message.reply_text(answer)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image files sent as documents"""
    doc = update.message.document
    if doc.mime_type and doc.mime_type.startswith("image/"):
        file = await doc.get_file()
        file_url = file.file_path
        
        await update.message.reply_text("📖 Reading image...")
        await update.message.reply_chat_action(action="typing")
        
        caption = update.message.caption
        answer = await get_answer_from_image(file_url, caption)
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text("❌ Please send an image file (JPEG, PNG, JPG)")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**How to use:**\n\n"
        "1️⃣ Send a text question\n"
        "2️⃣ Send a photo of a question\n"
        "3️⃣ Add a caption to an image if you want to ask something specific\n\n"
        "**Examples:**\n"
        "• `What is the square root of 144?`\n"
        "• Send a photo of `2x + 5 = 15`\n"
        "• Send a worksheet photo with caption `Question #4`\n\n"
        "Bot replies with **only the answer**.",
        parse_mode="Markdown"
    )

def main():
    print("🤖 Starting Worksheet Answer Bot...")
    print("Using GPT-4o (vision) - No OCR required!")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    
    print("✅ Bot is running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()
