import os
import logging
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate tokens exist
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai.api_key = OPENAI_API_KEY

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Models
TEXT_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo" for even cheaper
VISION_MODEL = "gpt-4o-mini"  # supports images

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    await update.message.reply_text(
        "🤖 **Worksheet Answer Bot**\n\n"
        "Send me:\n"
        "• Any text question\n"
        "• A photo of a worksheet or exam\n\n"
        "I'll reply with **only the answer** - no explanations.\n\n"
        "Made with GPT-4o-mini (reads images directly)",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text(
        "**How to use:**\n\n"
        "1️⃣ Send a text question like: `What is the capital of France?`\n"
        "2️⃣ Send a photo of a math problem, multiple choice, or any worksheet\n"
        "3️⃣ Add a caption to an image if you want to ask something specific\n\n"
        "**Examples:**\n"
        "• `2x + 5 = 15`\n"
        "• Photo of `What is the square root of 144?`\n"
        "• Worksheet photo with caption `Question #4`\n\n"
        "Bot replies with **only the answer**.",
        parse_mode="Markdown"
    )

async def get_answer_from_text(question: str) -> str:
    """Call GPT to answer directly (no explanations)."""
    try:
        response = openai.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an answer bot. Respond with ONLY the final answer. No explanations, no extra text, no 'Answer:' prefix. Just the answer."
                },
                {"role": "user", "content": question}
            ],
            temperature=0.1,
            max_tokens=500
        )
        answer = response.choices[0].message.content.strip()
        logger.info(f"Question: {question[:50]}... | Answer: {answer[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"OpenAI text error: {str(e)}")
        return f"❌ Error: {str(e)}"

async def get_answer_from_image(image_url: str, question_hint: str = None) -> str:
    """Call GPT-4o-mini to read image and answer directly."""
    try:
        user_content = [
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
        
        prompt = question_hint if question_hint else "Answer the question in this image. Provide only the final answer, no explanation."
        user_content.append({"type": "text", "text": prompt})
        
        response = openai.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You read text from images and answer questions directly. Respond with ONLY the answer. No explanations, no extra text."
                },
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=500
        )
        answer = response.choices[0].message.content.strip()
        logger.info(f"Image answered: {answer[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"OpenAI vision error: {str(e)}")
        return f"❌ Error: {str(e)}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    question = update.message.text
    await update.message.reply_chat_action(action="typing")
    answer = await get_answer_from_text(question)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages."""
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
    """Handle image files sent as documents."""
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    logger.info("Starting Worksheet Answer Bot...")
    logger.info(f"Using text model: {TEXT_MODEL}")
    logger.info(f"Using vision model: {VISION_MODEL}")
    
    # Create application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    app.add_error_handler(error_handler)
    
    # Start polling
    logger.info("Bot is running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
