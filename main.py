import telebot
import requests
import sqlite3
from datetime import datetime

my_bot = telebot.TeleBot("7629743821:AAFhmrFyDsJ-9f3KtoiHxdzgm-HvNlsZ0HY")
weather_API = 'a4f0b6f680c3ca3b3a6292b528dd923c'

def get_weather_from_db(city):
    conn = sqlite3.connect('weather_cache.db')
    c = conn.cursor()
    c.execute('SELECT * FROM weather WHERE city = ?', (city,))
    data = c.fetchone()
    conn.close()
    return data

def save_weather_to_db(city, temperature, humidity, wind_speed, description):
    last_updated = datetime.now()
    conn = sqlite3.connect('weather_cache.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO weather (city, temperature, humidity, wind_speed, description, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (city, temperature, humidity, wind_speed, description, last_updated))
    conn.commit()
    conn.close()

@my_bot.message_handler(commands=['start', 'main'])
def start(message):
    my_bot.send_message(message.chat.id,
                        "Вас приветствует бот - помощник. Введите команду /help для получения данных о моих способностях")

@my_bot.message_handler(commands=['help'])
def help(message):
    my_bot.send_message(message.chat.id, "У меня не так много команд, но тебе явно понравится! Попробуй команду /forecast.")

@my_bot.message_handler(commands=['forecast'])
def forecast(message):
    my_bot.send_message(message.chat.id, "Эта команда волшебством узнает информацию о погоде на любой точке планеты! Попробуй!")
    my_bot.send_message(message.chat.id, "Важное примечание: город необходимо писать на английском, с заглавной буквы, например: London")

@my_bot.message_handler(content_types=['text'])
def get_city(message):
    city_name = message.text.strip().lower()

    # Проверка наличия данных
    data = get_weather_from_db(city_name)

    if data:
        # Если есть
        my_bot.reply_to(message,
                        f'На данный момент в городе {data[0].title()}:\n'
                        f'Температура: {data[1]}°C\n'
                        f'Влажность: {data[2]}%\n'
                        f'Скорость ветра: {data[3]} м/с\n'
                        f'Описание: {data[4].capitalize()}')
    else:
        # Запрос к OpenWeatherMap
        result = requests.get(
            f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_API}&units=metric')

        if result.status_code == 200:
            weather_data = result.json()
            city = weather_data['name']
            country = weather_data['sys']['country']
            temperature = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            weather_description = weather_data['weather'][0]['description']
            wind_speed = weather_data['wind']['speed']
            humidity = weather_data['main']['humidity']

            # Сохраняем
            save_weather_to_db(city_name, temperature, humidity, wind_speed, weather_description)

            # Формируем ответ
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
            my_bot.reply_to(message, 'Неверно указан город! Попробуй еще раз!')


my_bot.polling(none_stop=True)

conn.close()