
import os

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    RSS_FEEDS_FILE = "rss_feeds.txt"
    MAX_NEWS_ITEMS = 30
    MAX_CHARS_FOR_ANALYSIS = 8000
    TG_MAX_MESSAGE_LENGTH = 4096
    COMMAND_COOLDOWN_SECONDS = 30

config = Config()
