import telebot
import requests
import sqlite3
from datetime import datetime

my_bot = telebot.TeleBot("7629743821:AAFhmrFyDsJ-9f3KtoiHxdzgm-HvNlsZ0HY")
weather_API = 'a4f0b6f680c3ca3b3a6292b528dd923c'


def create_weather_table():
    """Создает таблицу для хранения данных о погоде."""
    try:
        conn = sqlite3.connect('weather_cache.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS weather (
                city TEXT PRIMARY KEY,
                temperature REAL,
                humidity INTEGER,
                wind_speed REAL,
                description TEXT,
                last_updated DATETIME
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        conn.close()


def get_weather_from_db(city):
    """Получает данные о погоде из базы данных по названию города."""
    try:
        conn = sqlite3.connect('weather_cache.db')
        c = conn.cursor()
        c.execute('SELECT * FROM weather WHERE city = ?', (city,))
        data = c.fetchone()
        return data
    except sqlite3.Error as e:
        print(f"Ошибка при обращении к базе данных: {e}")
        return None
    finally:
        conn.close()


def save_weather_to_db(city, temperature, humidity, wind_speed, description):
    """Сохраняет данные о погоде в базу данных."""
    last_updated = datetime.now()
    try:
        conn = sqlite3.connect('weather_cache.db')
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO weather (city, temperature, humidity, wind_speed, description, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (city, temperature, humidity, wind_speed, description, last_updated))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении данных в базу: {e}")
    finally:
        conn.close()


@my_bot.message_handler(commands=['start', 'main'])
def start(message):
    """Обрабатывает команду /start и /main."""
    my_bot.send_message(
        message.chat.id,
        "Вас приветствует бот - помощник. Введите команду /help для информации о том, что я могу."
    )


@my_bot.message_handler(commands=['help'])
def help_command(message):
    """Обрабатывает команду /help."""
    my_bot.send_message(message.chat.id, "У меня есть единственная способность - узнавать погоду на любой точке планеты.")
    my_bot.send_message(message.chat.id, "Попробуй команду /forecast")


@my_bot.message_handler(commands=['forecast'])
def forecast_command(message):
    """Обрабатывает команду /forecast."""
    my_bot.send_message(message.chat.id, "Введи название интересующего тебя города.")


@my_bot.message_handler(content_types=['text'])
def get_city(message):
    """Обрабатывает текстовые сообщения с названием города."""
    city_name = message.text.strip().lower()

    # Проверка наличия данных в базе данных
    data = get_weather_from_db(city_name)

    if data:
        # Если данные найдены
        my_bot.reply_to(message,
                        f'На данный момент в городе {data[0].title()}:\n'
                        f'Температура: {data[1]}°C\n'
                        f'Влажность: {data[2]}%\n'
                        f'Скорость ветра: {data[3]} м/с\n'
                        f'Описание: {data[4].capitalize()}')
    else:
        # Запрос к API OpenWeatherMap
        try:
            result = requests.get(
                f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_API}&units=metric'
            )

            if result.status_code == 200:
                weather_data = result.json()
                city = weather_data['name']
                country = weather_data['sys']['country']
                temperature = weather_data['main']['temp']
                feels_like = weather_data['main']['feels_like']
                weather_description = weather_data['weather'][0]['description']
                wind_speed = weather_data['wind']['speed']
                humidity = weather_data['main']['humidity']

                # Сохраняем данные в базу данных
                save_weather_to_db(city_name, temperature, humidity, wind_speed, weather_description)

                # Формируем ответ для пользователя
                response_message = (
                    f"Погода в {city}, {country}:\n"
                    f"Температура: {temperature}°C\n"
                    f"Ощущается как: {feels_like}°C\n"
                    f"Описание: {weather_description.capitalize()}\n"
                    f"Скорость ветра: {wind_speed} м/с\n"
                    f"Влажность: {humidity}%"
                )
                my_bot.reply_to(message, response_message)
            else:
                my_bot.reply_to(message, 'Неверно указан город!')
        except requests.RequestException as e:
            my_bot.reply_to(message, 'Ошибка при обращении к API погоды. Попробуйте позже.')
            print(f"Ошибка запроса к API: {e}")


# Создаем таблицу при запуске
create_weather_table()

my_bot.polling(none_stop=True)