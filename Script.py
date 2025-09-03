import tweepy
import telebot
import time
import os
from dotenv import load_dotenv

load_dotenv() 

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = "StreamDatabase"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = "-1002685409854"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

last_sent_tweet_id = None

def get_latest_tweets():
    """Получает последние твиты пользователя."""
    user = client.get_user(username=TWITTER_USERNAME)
    user_id = user.data.id
    response = client.get_users_tweets(user_id, max_results=5)
    return response.data


def send_to_telegram(text):
    """Отправляет текст в Telegram-канал."""
    try:
        bot.send_message(TELEGRAM_CHANNEL_ID, text)
        print("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")

def main():
    """Основной цикл программы."""
    global last_sent_tweet_id
    print("Парсер запущен...")
    tweets = get_latest_tweets()
    if tweets:
        last_sent_tweet_id = tweets[0].id

    while True:
        try:
            tweets = get_latest_tweets()
            if tweets and tweets[0].id != last_sent_tweet_id:
                latest_tweet = tweets[0]
                print(f"Найден новый твит: {latest_tweet.text}")
                tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{latest_tweet.id}"
                send_to_telegram(f"{latest_tweet.text}\n\n{tweet_url}")
                last_sent_tweet_id = latest_tweet.id
            time.sleep(1800)
        except tweepy.TooManyRequests:
            print("Достигнут лимит запросов")
            time.sleep(1800)
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()