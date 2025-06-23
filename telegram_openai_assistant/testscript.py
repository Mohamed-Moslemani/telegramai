from dotenv import load_dotenv
import os

load_dotenv()

print("TELEGRAM_TOKEN_BOT:", os.getenv("TELEGRAM_TOKEN"))
print("ASSISTANT_ID_BOT:", os.getenv("ASSISTANT_ID"))
print("CLIENT_API_KEY:", os.getenv("CLIENT_API_KEY"))
