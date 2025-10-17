import os
from dotenv import load_dotenv
import telebot
from telebot import types
from database import save_user_to_db
from request import get_vacancies

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"
    user_nickname = message.from_user.username or None

    # Сохраняем пользователя в БД
    save_user_to_db(user_id, user_name, user_nickname)

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
        "💼 Введи ключевое слово для поиска (например: 'Python', 'Дизайнер'):"
    )
    bot.register_next_step_handler(message, get_keyword)


def get_keyword(message):
    keyword = message.text.strip()
    user_data[message.chat.id]['keyword'] = keyword

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Без опыта", callback_data="noExperience")
    btn2 = types.InlineKeyboardButton("1–3 года", callback_data="between1And3")
    btn3 = types.InlineKeyboardButton("3–6 лет", callback_data="between3And6")
    btn4 = types.InlineKeyboardButton("Более 6 лет", callback_data="moreThan6")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id, "📊 Укажи уровень опыта:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["noExperience", "between1And3", "between3And6", "moreThan6"])
def experience_selected(call):
    chat_id = call.message.chat.id
    experience = call.data
    user_data[chat_id]['experience'] = experience

    city = user_data[chat_id]['city']
    keyword = user_data[chat_id]['keyword']

    bot.edit_message_text("🔍 Ищу вакансии...", chat_id=chat_id, message_id=call.message.message_id)

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
    v = vacancies[index]

    text = (
        f"📌 <b>{v['name']}</b>\n"
        f"🏢 {v['employer']}\n"
        f"💰 Зарплата: {v['salary']}\n"
        f"🔗 [Перейти к вакансии]({v['alternate_url']})"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➡️ Далее", callback_data="next"),
        types.InlineKeyboardButton("🔗 Перейти", url=v['alternate_url'])
    )

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "next")
def next_vacancy(call):
    chat_id = call.message.chat.id
    user = user_data.get(chat_id)
    if not user:
        bot.answer_callback_query(call.id, "Ошибка. Начни с /start.")
        return

    user["index"] += 1
    if user["index"] >= len(user["vacancies"]):
        bot.send_message(chat_id, "🎉 Больше вакансий нет.")
    else:
        send_vacancy(chat_id)


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.polling(non_stop=True)