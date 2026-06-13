import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPT-4o can see images directly
GPT_MODEL = "gpt-4o"  # or "gpt-4o-mini" (cheaper, also supports vision)
