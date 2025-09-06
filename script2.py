import tweepy
import telebot
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timezone


# Загрузка переменных окружения
load_dotenv()
print("Переменные окружения загружены.")

# НАСТРОЙКИ TWITTER API
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = "Your_twitter_name"  # Имя пользователя в Twitter

# НАСТРОЙКИ TELEGRAM БОТА
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = "@your_channel_name" # ID или @username вашего канала

print("Все настройки успешно загружены.")

# ИНИЦИАЛИЗАЦИЯ
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)
print("Клиенты API для Twitter и Telegram инициализированы.")

last_sent_tweet_id = None

def get_latest_tweets(since_id=None):
    print("Вызвана функция get_latest_tweets...")
    now_utc = datetime.now(timezone.utc)
    start_of_day = now_utc.replace(hour=0,minute=0,second=0,microsecond=0)
    start_time_iso = start_of_day.isoformat()
    print(f"Запрашиваю ID для пользователя: {TWITTER_USERNAME}")
    user_response = client.get_user(username=TWITTER_USERNAME)
    if user_response.data is None:
        print(f"ОШИБКА: Не удалось получить данные для пользователя '{TWITTER_USERNAME}'.")
        print("Возможные причины: аккаунт защищен (приватный), заблокирован или не существует.")
        return None
    user_id = user_response.data.id
    print(f"ID пользователя получен: {user_id}")
    
    print(f"Запрашиваю последние 5 твитов для ID: {user_id}")
    response = client.get_users_tweets(user_id, max_results=5,since_id=since_id)
    print("Ответ от Twitter API получен.")
    return response.data

def send_to_telegram(text):
    print("Вызвана функция send_to_telegram...")
    print(f"Пытаюсь отправить сообщение в канал: {TELEGRAM_CHANNEL_ID}")
    try:
        bot.send_message(TELEGRAM_CHANNEL_ID, text)
        print("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        print(f"ОШИБКА при отправке в Telegram: {e}")

def main():
    global last_sent_tweet_id
    print("\nПарсер запущен.")

    try:
        tweets = get_latest_tweets(since_id=None)
        if tweets:
            last_sent_tweet_id = tweets[0].id
            print(f"Начальный ID твита установлен: {last_sent_tweet_id}")
        else:
            print("Не удалось получить твиты при первом запуске.")

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при первом запуске: {e}")
        return

    print("-" * 40)
    while True:
        print("\nНачинаю новый цикл проверки...")
        try:
            tweets = get_latest_tweets(since_id=last_sent_tweet_id)
            
            if tweets:
                # обрабатываем твиты от старых к новым, чтобы сохранить порядок
                for tweet in reversed(tweets):
                    print(f"Найден новый твит! ID: {tweet.id}")
                    print(f"Текст: {tweet.text[:80]}...")
                    
                    tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet.id}"
                    message_to_send = f"{tweet.text}\n\n{tweet_url}"
                    
                    send_to_telegram(message_to_send)
                    
                    # Обновляем ID после КАЖДОЙ отправки
                    last_sent_tweet_id = tweet.id
                    print(f"ID последнего твита обновлен на: {last_sent_tweet_id}")
                    time.sleep(1) 
                print(f"Новых твитов не найдено.")

        except tweepy.TooManyRequests as e:
            reset_timestamp_str = e.response.headers.get('x-rate-limit-reset')
            
            if reset_timestamp_str:
                reset_timestamp = int(reset_timestamp_str)
                current_timestamp = int(datetime.now(timezone.utc).timestamp())
                
                wait_time = reset_timestamp - current_timestamp
                
                wait_time = max(0, wait_time + 5) 
                
                print(f"Достигнут лимит запросов (429).")
                print(f"API разрешит запросы через {wait_time // 60} мин {wait_time % 60} сек.")
                time.sleep(wait_time)
            else:
                print("Достигнут лимит запросов (429). Жду 15 минут по умолчанию.")
                time.sleep(900)
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            print("Жду 5 минут перед повторной попыткой.")
            time.sleep(300)

        print(f"Пауза перед следующим циклом. Ожидание 30 минут...")
        time.sleep(1800)

if __name__ == "__main__":
    main()