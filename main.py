import os
import asyncio
import feedparser
import google.generativeai as genai
from telegram import Bot

TELEGRAM_TOKEN = "8895214469:AAG9_cIFsGD0-ZrNDyOzsZdBG6J8A_T7amQ"
GEMINI_API_KEY = "AQ.Ab8RN6JxTa4Yv9UjpMgjmfBWPSr-JSVk7h55_QluMGKUvBB2dyg"
CHANNEL_ID = "@Hamadsport_bot"

bot = Bot(token=TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

def translate_and_format(title, summary):
    prompt = f"""
    ئەم هەواڵە وەرزشییەی خوارەوە بکە بە کوردییەکی ڕوان، سەرنجڕاکێش و پوخت بۆ کەناڵی تیلیگرام.
    لەگەڵ دانانی هێمای گونجاو (Emoji).
    سەردێر: {title}
    دەق: {summary}
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

async def post_news():
    feed_url = "https://www.goal.com/feeds/news"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        return

    latest = feed.entries[0]
    title = latest.title
    link = latest.link
    summary = latest.get('summary', '')
    
    translated_text = translate_and_format(title, summary)
    final_message = f"{translated_text}\n\n🔗 **سەرچاوە:** [Goal.com]({link})"
    
    image_url = None
    if 'media_content' in latest:
        image_url = latest.media_content[0]['url']
    elif 'enclosures' in latest and latest.enclosures:
        image_url = latest.enclosures[0].get('href')

    async with bot:
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=final_message, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=final_message, parse_mode="Markdown")

asyncio.run(post_news())
