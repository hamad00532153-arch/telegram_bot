# ============================================================
# HAMAD SPORT NEWS BOT
# Football News -> Kurdish -> Telegram
# Render + Flask + Gemini + RSS
# ============================================================

import os
import json
import asyncio
import logging
import threading

import feedparser
from flask import Flask
from google import genai
from telegram import Bot


# ============================================================
# FLASK / RENDER WEB SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "HAMAD SPORT NEWS BOT is running! ✅"


@app.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
    host="0.0.0.0",
    port=port,
    use_reloader=False
    )
FEED_URLS = [
    "https://www.goal.com/feeds/news",
    "https://arabic.rt.com/rss/sport/",
]

# ============================================================
# SETTINGS
# ============================================================



# ============================================================
# SETTINGS
# ============================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ناوی کەناڵەکەت
CHANNEL_USERNAME = "@Hamadsport_bot"

# RSS
#FEED_URL = "https://www.goal.com/feeds/news"

# فایلەکە بۆ هەواڵە پۆستکراوەکان
SEEN_FILE = "seen_news.json"

# هەر 5 خولەک
CHECK_INTERVAL = 300

# Gemini
GEMINI_MODEL = "gemini-3.6-flash"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("HamadSportBot")


# ============================================================
# CHECK CONFIG
# ============================================================

if not TELEGRAM_TOKEN:
    raise ValueError(
        "❌ TELEGRAM_TOKEN لە Environment Variables دانەنراوە."
    )

if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY لە Environment Variables دانەنراوە."
    )


# ============================================================
# CLIENTS
# ============================================================

bot = Bot(
    token=TELEGRAM_TOKEN
)

gemini = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# LOAD SEEN NEWS
# ============================================================

def load_seen_news():

    if not os.path.exists(SEEN_FILE):
        return set()

    try:

        with open(
            SEEN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return set(data)

        return set()

    except Exception as error:

        logger.error(
            f"❌ هەڵە لە خوێندنەوەی seen_news: {error}"
        )

        return set()


# ============================================================
# SAVE SEEN NEWS
# ============================================================

def save_seen_news(seen):

    try:

        # تەنها 500 هەواڵی کۆتایی
        data = list(seen)[-500:]

        with open(
            SEEN_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        logger.error(
            f"❌ هەڵە لە پاشەکەوتکردنی هەواڵەکان: {error}"
        )


# ============================================================
# GET IMAGE FROM RSS
# ============================================================

def get_image_url(entry):

    # media_content
    media_content = entry.get(
        "media_content",
        []
    )

    for media in media_content:

        url = media.get("url")

        if url:
            return url


    # media_thumbnail
    media_thumbnail = entry.get(
        "media_thumbnail",
        []
    )

    for media in media_thumbnail:

        url = media.get("url")

        if url:
            return url


    # links
    links = entry.get(
        "links",
        []
    )

    for link in links:

        href = link.get("href")
        link_type = link.get("type", "")

        if href and link_type.startswith("image/"):
            return href


    # enclosures
    enclosures = entry.get(
        "enclosures",
        []
    )

    for enclosure in enclosures:

        url = enclosure.get("href")

        if url:
            return url


    return None


# ============================================================
# GEMINI
# ============================================================

def translate_and_format(title, summary):

    prompt = f"""
تۆ نووسەرێکی پڕۆفیشنەڵی هەواڵی وەرزشییت.

ئەم هەواڵەی خوارەوە وەرگێڕە بۆ زمانی کوردیی سۆرانی
و بۆ پۆستی Telegram بە شێوەیەکی پڕۆفیشنەڵ ئامادەی بکە.

مەرجەکان:

1. مانای ڕاستەقینەی هەواڵەکە بپارێزە.
2. هیچ زانیارییەکی خۆت زیاد مەکە.
3. هەواڵەکە کورت و خۆشخوێن بێت.
4. سەردێڕێکی سەرنجڕاکێش بنووسە.
5. ناوی یاریزان و یانەکان بە دروستی بپارێزە.
6. ژمارە و بەروارەکان بە دروستی بپارێزە.
7. هەواڵەکە 2 تا 5 پاراگراف بێت.
8. هیچ هاشتاکێک زیاد مەکە.
9. هیچ لینکێک لە ناو دەقی هەواڵەکەدا مەخە.
10. تەنها زمانی کوردی بەکاربهێنە جگە لە ناوی یاریزان و یانەکان.
11. دەقەکە سروشتی بێت، نەک وەرگێڕانی وشە بە وشە.
12. هیچ وشەیەک وەک "بەپێی ئەم دەقە" یان "وەرگێڕان" مەنووسە.

شێوازی دەرچوون:

⚽ سەردێڕ:
[سەردێڕ]

📰 هەواڵ:
[دەقی هەواڵ]

هەواڵی سەرچاوە:

Title:
{title}

Summary:
{summary}
"""

    try:

        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if not response or not response.text:

            logger.error(
                "❌ Gemini هیچ وەڵامێکی نەدا."
            )

            return None

        return response.text.strip()

    except Exception as error:

        logger.error(
            f"❌ Gemini error: {error}"
        )

        return None


# ============================================================
# GET NEWS
# ============================================================

def get_news():

    try:

        logger.info(
            "🔎 پشکنینی RSS بۆ هەواڵی نوێ..."
        )

        news_list = []

        for feed_url in FEED_URLS:

            try:

                feed = feedparser.parse(
                    feed_url
                )

                if not feed.entries:
                    continue

                for entry in feed.entries:

                    title = entry.get(
                        "title",
                        ""
                    ).strip()

                    summary = entry.get(
                        "summary",
                        ""
                    ).strip()

                    link = entry.get(
                        "link",
                        ""
                    ).strip()

                    news_id = entry.get(
                        "id",
                        ""
                    ).strip()

                    if not news_id:
                        news_id = link

                    if not news_id:
                        news_id = title

                    image = get_image_url(
                        entry
                    )

                    if not title:
                        continue

                    news_list.append(
                        {
                            "id": news_id,
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "image": image
                        }
                    )

            except Exception as e:

                logger.error(
                    f"❌ RSS error with {feed_url}: {e}"
                )

        if not news_list:

            logger.warning(
                "⚠️ هیچ هەواڵێک لە سەرچاوەکان نەدۆزرایەوە."
            )

            return []

        return news_list

    except Exception as error:

        logger.error(
            f"❌ RSS error: {error}"
        )

        return []


# ============================================================
# SEND NEWS
# ============================================================

async def send_news(news):

    logger.info(
        f"📰 ئامادەکردنی: {news['title']}"
    )

    translated = translate_and_format(
        news["title"],
        news["summary"]
    )

    if not translated:

        logger.error(
            "❌ وەرگێڕان سەرکەوتوو نەبوو."
        )

        return False


    source_link = news["link"]

    message = (
        f"{translated}\n\n"
        f"🔗 سەرچاوە:\n"
        f"{source_link}"
    )


    # ========================================================
    # PHOTO
    # ========================================================

    if news["image"]:

        try:

            caption = message

            if len(caption) > 1024:

                caption = (
                    translated[:850]
                    + f"\n\n🔗 سەرچاوە:\n{source_link}"
                )

            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=news["image"],
                caption=caption
            )

            logger.info(
                "✅ وێنە + هەواڵ نێردرا."
            )

            return True

        except Exception as error:

            logger.warning(
                f"⚠️ ناردنی وێنە سەرکەوتوو نەبوو: {error}"
            )


    # ========================================================
    # TEXT
    # ========================================================

    try:

        if len(message) > 4096:

            message = (
                translated[:3800]
                + f"\n\n🔗 سەرچاوە:\n{source_link}"
            )

        await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=message
        )

        logger.info(
            "✅ هەواڵ بەبێ وێنە نێردرا."
        )

        return True

    except Exception as error:

        logger.error(
            f"❌ Telegram error: {error}"
        )

        return False


# ============================================================
# PROCESS NEWS
# ============================================================

async def process_news():

    seen = load_seen_news()

    news_list = get_news()

    if not news_list:
        return

    new_news = []

    for news in news_list:

        if news["id"] not in seen:

            new_news.append(news)

    if not new_news:

        logger.info(
            "ℹ️ هیچ هەواڵێکی نوێ نییە."
        )

        return

    logger.info(
        f"🔥 {len(new_news)} هەواڵی نوێ دۆزرایەوە. دەستپێکردنی پۆستکردن..."
    )

    # کۆنترین -> نوێترین
    for news in reversed(new_news):

        success = await send_news(news)

        if success:

            seen.add(
                news["id"]
            )

            save_seen_news(
                seen
            )

            logger.info(
                "💾 هەواڵەکە وەک پۆستکراو تۆمار کرا."
            )

            # چاوەڕوانکردنی ١٢٠ چرکە (٢ دەقە) بۆ هەواڵی داهاتوو
            await asyncio.sleep(120)

        else:

            logger.warning(
                "⚠️ هەواڵەکە نەنێردرا؛ "
                "دواتر هەوڵی دووبارە دەدرێت."
            )
            await asyncio.sleep(10)

# ============================================================
# TEST TELEGRAM
# ============================================================

async def test_telegram():

    try:

        me = await bot.get_me()

        logger.info(
            f"✅ Telegram Bot connected: @{me.username}"
        )

        return True

    except Exception as error:

        logger.error(
            f"❌ Telegram connection failed: {error}"
        )

        return False


# ============================================================
# MAIN BOT
# ============================================================

async def main():

    logger.info(
        "================================================"
    )

    logger.info(
        "🚀 HAMAD SPORT NEWS BOT STARTED"
    )

    logger.info(
        "================================================"
    )

    logger.info(
        f"📢 Channel: {CHANNEL_USERNAME}"
    )

    logger.info(
        f"🌐 RSS: {FEED_URLS[0]}"
    )

    logger.info(
        f"⏱️ Check: every {CHECK_INTERVAL} seconds"
    )


    # Telegram test
    telegram_ok = await test_telegram()

    if not telegram_ok:

        logger.error(
            "🛑 Bot ناتوانێت بە Telegram پەیوەندی بکات."
        )

        return


    # Main loop
    while True:

        try:

            await process_news()

        except Exception as error:

            logger.exception(
                f"❌ Unexpected error: {error}"
            )


        logger.info(
            f"💤 چاوەڕوانی {CHECK_INTERVAL} چرکە..."
        )

        await asyncio.sleep(
            CHECK_INTERVAL
        )


# ============================================================
# START BOT THREAD
# ============================================================

def start_bot():

    try:

        asyncio.run(
            main()
        )

    except Exception as error:

        logger.exception(
            f"❌ Bot stopped: {error}"
        )


# ============================================================
# START EVERYTHING
# ============================================================

if __name__ == "__main__":

    # Flask لە thread ـێکی جیاواز
    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()


    # Telegram bot
    start_bot()