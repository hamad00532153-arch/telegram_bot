import os
import time
import feedparser
import google.generativeai as genai
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("8895214469:AAG9_cIFsGD0-ZrNDyOzsZdBG6J8A_T7amQ")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6JxTa4Yv9UjpMgjmfBWPSr-JSVk7h55_QluMGKUvBB2dyg")
CHANNEL_USERNAME = "@Hamadsport_bot"

genai.configure(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def translate_and_format(title, summary):
    prompt = f"Translate and summarize this news to Kurdish smoothly: Title: {title} Summary: {summary}"
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def get_image_url(entry):
    # پشکنین بۆ دۆزینەوەی وێنە لە ناو فیدەکەدا
    if 'media_content' in entry and len(entry['media_content']) > 0:
        return entry['media_content'][0].get('url')
    if 'links' in entry:
        for link in entry['links']:
            if 'image' in link.get('type', ''):
                return link.get('href')
    return None

def check_news():
    feed_url = "https://www.goal.com/feeds/news"
    feed = feedparser.parse(feed_url)
    if feed.entries:
        latest = feed.entries[0]
        title = latest.title
        summary = latest.get('summary', '')
        link = latest.link
        
        translated_text = translate_and_format(title, summary)
        image_url = get_image_url(latest)
        
        message = f"⚽ **هەواڵی وەرزشی**\n\n{translated_text}\n\n🔗 **سەرچاوە:** [Goal.com]({link})"
        
        # ئەگەر هەواڵەکە وێنەی هەبوو، وێنە و دەقەکە بەیەکەوە پۆست دەکات (خاڵی ٤)
        if image_url:
            bot.send_photo(chat_id=CHANNEL_USER-NAME, photo=image_url, caption=message, parse_mode="Markdown")
        else:
            bot.send_message(chat_id=CHANNEL_USER-NAME, text=message, parse_mode="Markdown")
