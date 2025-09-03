import tweepy
import telebot
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# --- Загрузка переменных окружения ---
load_dotenv()
print("[LOG] Переменные окружения загружены.")

# --- НАСТРОЙКИ TWITTER API ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = "StreamDatabase"  # Имя пользователя в Twitter

# --- НАСТРОЙКИ TELEGRAM БОТА ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = "@your_channel_name" # ID или @username вашего канала

print("[LOG] Все настройки успешно загружены.")

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)
print("[LOG] Клиенты API для Twitter и Telegram инициализированы.")

# --- Глобальная переменная для ID последнего твита ---
last_sent_tweet_id = None

def get_latest_tweets():
    """Получает последние твиты пользователя."""
    print("  [FUNC] Вызвана функция get_latest_tweets...")
    now_utc = datetime.now(timezone.utc)
    start_of_day = now_utc.replace(hour=0,minute=0,second=0,microsecond=0)
    start_time_iso = start_of_day.isoformat()
    print(f"    [API] Запрашиваю ID для пользователя: {TWITTER_USERNAME}")
    user_response = client.get_user(username=TWITTER_USERNAME)
    if user_response.data is None:
        print(f"    [API] ❌ ОШИБКА: Не удалось получить данные для пользователя '{TWITTER_USERNAME}'.")
        print("      Возможные причины: аккаунт защищен (приватный), заблокирован или не существует.")
        return None
    user_id = user_response.data.id
    print(f"    [API] ID пользователя получен: {user_id}")
    
    print(f"    [API] Запрашиваю последние 5 твитов для ID: {user_id}")
    response = client.get_users_tweets(user_id, max_results=5, start_time=start_time_iso)
    print("    [API] Ответ от Twitter API получен.")
    return response.data

def send_to_telegram(text):
    """Отправляет текст в Telegram-канал."""
    print("  [FUNC] Вызвана функция send_to_telegram...")
    print(f"    [SEND] Пытаюсь отправить сообщение в канал: {TELEGRAM_CHANNEL_ID}")
    try:
        bot.send_message(TELEGRAM_CHANNEL_ID, text)
        print("    [SEND] ✅ Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        print(f"    [SEND] ❌ ОШИБКА при отправке в Telegram: {e}")

def main():
    """Основной цикл программы."""
    global last_sent_tweet_id
    print("\n[INIT] Парсер запущен. Выполняю первую проверку для установки начального твита...")

    try:
        tweets = get_latest_tweets()
        if tweets:
            last_sent_tweet_id = tweets[0].id
            print(f"[INIT] Начальный ID твита установлен: {last_sent_tweet_id}")
        else:
            print("[INIT] Не удалось получить твиты при первом запуске.")
    except Exception as e:
        print(f"[INIT] ❌ КРИТИЧЕСКАЯ ОШИБКА при первом запуске: {e}")
        return # Завершаем работу, если не можем начать

    print("-" * 40)

    while True:
        print("\n[LOOP] Начинаю новый цикл проверки...")
        try:
            tweets = get_latest_tweets()
            
            if not tweets:
                print("  [CHECK] API не вернул твиты. Пропускаю итерацию.")
            elif tweets[0].id == last_sent_tweet_id:
                print(f"  [CHECK] Новых твитов не найдено. Последний ID: {last_sent_tweet_id}")
            else:
                print(f"  [CHECK] 🔥 Найден новый твит! ID: {tweets[0].id}")
                latest_tweet = tweets[0]
                print(f"    [CONTENT] Текст: {latest_tweet.text[:80]}...")
                
                tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{latest_tweet.id}"
                message_to_send = f"{latest_tweet.text}\n\n{tweet_url}"
                
                send_to_telegram(message_to_send)
                
                last_sent_tweet_id = latest_tweet.id
                print(f"  [UPDATE] ID последнего отправленного твита обновлен на: {last_sent_tweet_id}")

        except tweepy.TooManyRequests:
            print("  [ERROR] ⏳ Достигнут лимит запросов (429). Жду 15 минут.")
            time.sleep(900)
        except Exception as e:
            print(f"  [ERROR] ❌ Произошла непредвиденная ошибка: {e}")
            print("    [RETRY] Жду 5 минут перед повторной попыткой.")
            time.sleep(300)

        print(f"[LOOP] Пауза перед следующим циклом. Ожидание 30 минут...")
        time.sleep(1800)

if __name__ == "__main__":
    main()