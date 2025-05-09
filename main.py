import telebot
import requests
import json

my_bot = telebot.TeleBot("7629743821:AAFhmrFyDsJ-9f3KtoiHxdzgm-HvNlsZ0HY")
weather_API = 'a4f0b6f680c3ca3b3a6292b528dd923c'


@my_bot.message_handler(commands=['start', 'main'])
def start(message):
    my_bot.send_message(message.chat.id, "Вас приветствует бот - помощник. Введите название города")


@my_bot.message_handler(content_type=['text'])
def get_city(message):
    city_name = message.text.strip().lower()
    result = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_API}&units=metric')
    if result.status_code == 200:
        data = json.loads(result.text)
        temperature = data["main"]["temp"]
        my_bot.reply_to(message, f'На данный момент погода: {temperature}')
    else:
        my_bot.reply_to(message, 'Неверно указан город!')


my_bot.polling(none_stop=True)
