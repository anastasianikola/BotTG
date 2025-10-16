# bot.py
import telebot
from telebot import types

from config import TOKEN
from request import get_vacancies

bot = telebot.TeleBot(TOKEN)
user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе найти вакансии с hh.ru.\n\n"
        "📍 Введи город, в котором хочешь искать работу:"
    )
    bot.register_next_step_handler(message, get_city)


def get_city(message):
    city = message.text.strip()
    user_data[message.chat.id] = {'city': city}

    bot.send_message(
        message.chat.id,
        "💼 Введи ключевое слово для поиска (например: 'Python', 'Дизайнер', 'Менеджер'):"
    )
    bot.register_next_step_handler(message, get_keyword)


def get_keyword(message):
    keyword = message.text.strip()
    user_data[message.chat.id]['keyword'] = keyword

    # 📊 Создаём кнопки для выбора опыта
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Без опыта", callback_data="noExperience")
    btn2 = types.InlineKeyboardButton("1–3 года", callback_data="between1And3")
    btn3 = types.InlineKeyboardButton("3–6 лет", callback_data="between3And6")
    btn4 = types.InlineKeyboardButton("Более 6 лет", callback_data="moreThan6")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(
        message.chat.id,
        "📊 Укажи уровень опыта:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in ["noExperience", "between1And3", "between3And6", "moreThan6"])
def experience_selected(call):
    chat_id = call.message.chat.id
    experience = call.data
    user_data[chat_id]['experience'] = experience

    city = user_data[chat_id]['city']
    keyword = user_data[chat_id]['keyword']

    bot.edit_message_text(
        "🔍 Ищу вакансии, подожди немного...",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

    vacancies = get_vacancies(city, keyword, experience)

    if not vacancies:
        bot.send_message(chat_id, "❌ Не удалось найти вакансии. Попробуй другой запрос.")
        return

    user_data[chat_id]['vacancies'] = vacancies
    user_data[chat_id]['index'] = 0

    send_vacancy(chat_id)


def send_vacancy(chat_id):
    vacancies = user_data[chat_id]["vacancies"]
    index = user_data[chat_id]["index"]

    vacancy = vacancies[index]
    name = vacancy['name']
    url = vacancy['alternate_url']
    employer = vacancy.get('employer', 'Не указано')
    salary_text = vacancy.get('salary', 'Не указана')

    text = f"📌 <b>{name}</b>\n🏢 {employer}\n💰 Зарплата: {salary_text}\n🔗 [Перейти к вакансии]({url})"

    markup = telebot.types.InlineKeyboardMarkup()
    btn_next = telebot.types.InlineKeyboardButton("➡️ Далее", callback_data="next")
    btn_link = telebot.types.InlineKeyboardButton("🔗 Перейти", url=url)
    markup.add(btn_next, btn_link)

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "next")
def next_vacancy(call):
    user = user_data.get(call.message.chat.id)
    if not user:
        bot.answer_callback_query(call.id, "Ошибка данных. Начни заново с /start.")
        return

    user["index"] += 1
    if user["index"] >= len(user["vacancies"]):
        bot.send_message(call.message.chat.id, "🎉 Это были все найденные вакансии.")
    else:
        send_vacancy(call.message.chat.id)


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.polling(non_stop=True)