import logging
import openai
import pytesseract
from PIL import Image
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, GPT_MODEL

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me text or an image - I'll answer!")

async def get_answer(question: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "Answer directly. Only the answer, no explanation."},
                {"role": "user", "content": question}
            ],
            temperature=0.1,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = await get_answer(update.message.text)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    
    await update.message.reply_text("Reading image...")
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        extracted = pytesseract.image_to_string(image)
        
        if not extracted.strip():
            await update.message.reply_text("Couldn't read text from image.")
            return
        
        answer = await get_answer(extracted)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"OCR failed: {str(e)}\n\nMake sure Tesseract is installed.\nWindows: Download from GitHub UB-Mannheim/tesseract")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
