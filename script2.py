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
TWITTER_USERNAME = "StreamDataBase"  # Имя пользователя в Twitter

# --- НАСТРОЙКИ TELEGRAM БОТА ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = "@TwitterBadgeParser"

# Фильтрация постов
SKIP_PHRASE = "Get notified on Discord"



print("[LOG] Все настройки успешно загружены.")

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
)
print("[LOG] Клиенты API для Twitter и Telegram инициализированы.")

# --- Глобальная переменная для ID последнего твита ---
last_sent_tweet_id = None


def get_latest_tweets(since_id=None):
    """Получает последние твиты пользователя."""
    print("  [FUNC] Вызвана функция get_latest_tweets...")
    now_utc = datetime.now(timezone.utc)
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time_iso = start_of_day.isoformat()
    print(f"    [API] Запрашиваю ID для пользователя: {TWITTER_USERNAME}")
    user_response = client.get_user(username=TWITTER_USERNAME)
    if user_response.data is None:
        print(
            f"    [API] ❌ ОШИБКА: Не удалось получить данные для пользователя '{TWITTER_USERNAME}'."
        )
        print(
            "      Возможные причины: аккаунт защищен (приватный), заблокирован или не существует."
        )
        return None
    user_id = user_response.data.id
    print(f"    [API] ID пользователя получен: {user_id}")

    print(f"    [API] Запрашиваю последние 5 твитов для ID: {user_id}")
    response = client.get_users_tweets(user_id, max_results=5, since_id=since_id)
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
    print(
        "\n[INIT] Парсер запущен. Выполняю первую проверку для установки начального твита..."
    )

    try:
        tweets = get_latest_tweets(since_id=None)
        if tweets:
            last_sent_tweet_id = tweets[0].id
            print(f"[INIT] Начальный ID твита установлен: {last_sent_tweet_id}")
        else:
            print("[INIT] Не удалось получить твиты при первом запуске.")
    except tweepy.TooManyRequests as e:
        print("[INIT] ⏳ Обнаружен активный лимит запросов при запуске.")
        reset_timestamp_str = e.response.headers.get("x-rate-limit-reset")

        if reset_timestamp_str:
            reset_timestamp = int(reset_timestamp_str)
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            wait_time = max(0, reset_timestamp - current_timestamp + 5)

            print(
                f"  [WAIT] API разрешит запросы через {wait_time // 60} мин {wait_time % 60} сек."
            )
            print("  [WAIT] Скрипт переходит в режим ожидания...")
            time.sleep(wait_time)
        else:
            print(
                "  [WAIT] Не удалось определить время сброса, жду 15 минут по умолчанию."
            )
            time.sleep(900)

    print("-" * 40)
    while True:
        print("\n[LOOP] Начинаю новый цикл проверки...")
        try:
            # Передаем ID последнего отправленного твита
            tweets = get_latest_tweets(since_id=last_sent_tweet_id)

            if tweets:
                # ВАЖНО: обрабатываем твиты от старых к новым, чтобы сохранить порядок
                for tweet in reversed(tweets):
                    print(f"  [CHECK] 🔥 Найден новый твит! ID: {tweet.id}")
                    print(f"    [CONTENT] Текст: {tweet.text[:80]}...")

                    if SKIP_PHRASE and tweet.text.lower().strip().startswith(SKIP_PHRASE.lower()):
                        print(f"    [SKIP] 🚫 Твит ID {tweet.id} начинается с запрещенной фразы. Пропускаю.")
                        continue

                    tweet_url = (
                        f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet.id}"
                    )
                    message_to_send = f"{tweet.text}\n\n{tweet_url}"

                    send_to_telegram(message_to_send)

                    # Обновляем ID после КАЖДОЙ отправки
                    last_sent_tweet_id = tweet.id
                    print(
                        f"  [UPDATE] ID последнего твита обновлен на: {last_sent_tweet_id}"
                    )
                    time.sleep(1)  # Небольшая пауза между отправкой нескольких твитов
            else:
                print(f"  [CHECK] Новых твитов не найдено.")

        except tweepy.errors.TweepyException as e:
            print("  [ERROR] ❌ Произошла ошибка API:")
            print(
                f"    [API Status]  Code: {e.response.status_code}, Reason: {e.response.reason}"
            )
            if e.api_errors:
                for error in e.api_errors:
                    print(
                        f"    [API Message] {error.get('title')}: {error.get('detail')}"
                    )
            else:
                print(f"    [API Raw]     {e.response.text}")
            print("    [RETRY] Жду 5 минут перед повторной попыткой.")
            time.sleep(300)

        except tweepy.TooManyRequests as e:  # 👈 ВОТ ИЗМЕНЕНИЯ
            # Получаем время сброса лимита из заголовков ответа
            reset_timestamp_str = e.response.headers.get("x-rate-limit-reset")

            if reset_timestamp_str:
                # Преобразуем строку в число
                reset_timestamp = int(reset_timestamp_str)
                # Получаем текущее время в UTC
                current_timestamp = int(datetime.now(timezone.utc).timestamp())

                # Вычисляем, сколько секунд осталось ждать
                wait_time = reset_timestamp - current_timestamp

                # Добавляем небольшой запас в 5 секунд на всякий случай
                wait_time = max(0, wait_time + 5)

                print(f"  [ERROR] ⏳ Достигнут лимит запросов (429).")
                print(
                    f"    [WAIT] API разрешит запросы через {wait_time // 60} мин {wait_time % 60} сек."
                )
                time.sleep(wait_time)
            else:
                # Если по какой-то причине заголовок не пришёл, ждём по старинке
                print(
                    "  [ERROR] ⏳ Достигнут лимит запросов (429). Жду 15 минут по умолчанию."
                )
                time.sleep(900)
        except Exception as e:
            print(f"  [ERROR] ❌ Произошла непредвиденная ошибка: {e}")
            print("    [RETRY] Жду 5 минут перед повторной попыткой.")
            time.sleep(300)

        print(f"[LOOP] Пауза перед следующим циклом. Ожидание 30 минут...")
        time.sleep(1800)


if __name__ == "__main__":
    main()
