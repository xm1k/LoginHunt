import re
import telebot
from matplotlib.style.core import available
from telebot import types
from config import TOKEN, yookassa_token, yookassa_shop_id, premium
from pick_logins import main
from yookassa import Payment
from threading import Thread
import yookassa
import json
import os
import asyncio
import queue

yookassa.Configuration.account_id = yookassa_shop_id
yookassa.Configuration.secret_key = yookassa_token

premium_source = "premium.json"
users_queue = queue.Queue()
results = {}
current = []
premium_count = 0

async def process_queue():
    while True:
        global premium_count
        try:
            user_id, usernames, isPremium = users_queue.get()
            if(user_id == -1):
                users_queue.task_done()
            else:
                available_usernames = await main(usernames, isPremium)
                results[user_id] = available_usernames
                if len(available_usernames) == 0:
                    bot.send_message(user_id, f"Не нашлось свободных логинов...")
                else:
                    bot.send_message(user_id, f"Найденные логины:\n\n" + '\n'.join([f"{i + 1}. {username}" for i, username in enumerate(available_usernames)]))
                if(not isPremium):
                    users_queue.task_done()
                else:
                    premium_count-=1
                current.remove(user_id)
        except Exception as e:
            print(e)
            bot.send_message(user_id, "Ошибка при обработке запроса...")
            users_queue.task_done()


def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_queue())

def load_premium_users():
    if os.path.exists(premium_source):
        with open(premium_source, "r") as f:
            return json.load(f)
    return []

def save_premium_users(users):
    with open(premium_source, "w") as f:
        json.dump(users, f)

def add_premium_user(user_id):
    if user_id not in premium:
        premium.append(int(user_id))
        save_premium_users(premium)

premium = load_premium_users()

def create_payment(amount, description):
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/login_hunt_bot"
        },
        "capture": True,
        "description": description
    })
    return payment

bot = telebot.TeleBot(TOKEN)
cost = 128;

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if(message.chat.id not in premium):
        button1 = types.KeyboardButton("🍪 Cookie")
        button2 = types.KeyboardButton("ℹ️ Помощь")
        markup.add(button1, button2)
    else:
        markup.add(types.KeyboardButton("ℹ️ Помощь"))
    bot.send_message(
        message.chat.id,
        """Привет!🤘 Я - бот по серфингу доступных логинов в телеграм

Как пользоваться:
1. Отправь мне слово или никнейм, который хочешь проверить. ✏️
2. Я проверю доступность этого имени в Telegram и сообщу тебе результат. 🔎
3. Если имя занято, я подберу похожие варианты или предложу что-то новое. 🍪

⚡️ Быстро, удобно и без усилий!""",
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if(message.text == "ℹ️ Помощь"):
        if(message.chat.id in premium):
            bot.send_message(message.chat.id, """🍪 Как пользоваться ботом:

Отправьте боту логин или несколько (до 5), которые хотите проверить. Я посмотрю, где они доступны 🔎""")
        elif(message.chat.id not in premium):
            bot.send_message(message.chat.id, f"""ℹ️ Как пользоваться ботом:

1. Отправьте боту слово или логин, который хотите проверить. Я посмотрю, доступен ли этот ник в Telegram.
2. Дождитесь своей очереди на выполнение задачи
3. Получите 10 первых доступных логинов

❗️ВАЖНО: Вывод программы не гарантирует доступность логина, пользователь может быть либо заблокирован либо закрыть доступ к аккаунту по логину, cookie исправляет эту проблему

🍪 Cookie функции:
Для cookie-пользователей доступны расширенные возможности:
- Логины проходят дополнительную проверку
- Все логины в выводе гарантированно доступны
- Обработка запроса без очереди
- Вывод 25 первых логинов, вместо 10
- Возможность проверить несколько логинов одним сообщением (до 5)
- Проверка логина на доступность в других соц. сетях

Просто напишите боту любое слово или никнейм — я сразу проверю его для вас!""")


    elif(message.text == "🍪 Cookie"):
        markup = types.InlineKeyboardMarkup()
        payment = create_payment(cost, "PREMIUM подписка")
        payment_url = payment.confirmation.confirmation_url
        button1 = types.InlineKeyboardButton("Купить 💰", url=payment_url)
        button2 = types.InlineKeyboardButton("Подтвердить покупку ✅", callback_data=f"confirm_{payment.id}_{message.chat.id}")
        markup.add(button1)
        markup.add(button2)
        bot.send_message(message.chat.id, f"""🍪 Cookie status

Для cookie-пользователей доступны расширенные возможности:
- Логины проходят дополнительную проверку
- Все логины в выводе гарантированно доступны
- Обработка запроса без очереди
- Вывод 25 первых логинов, вместо 10
- Возможность проверить несколько логинов одним сообщением (до 5)
- Проверка логина на доступность в других соц. сетях

Купить COOKIE навсегда за {cost} RUB 👇""", reply_markup=markup)

    else:
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]{3,8}[a-zA-Z0-9]$"
        alert = """Ошибка ввода ⚠️
Логины могут быть длиной 5-10 символов содержать только буквы a-Z, цифры и нижние подчеркивания, логин должен начинаться с буквы и не может заканчиваться на нижнее подчеркивание"""
        words = message.text.split(' ')
        if(message.chat.id not in current):
            if(message.chat.id not in premium):
                if(len(words)>1):
                    bot.send_message(message.chat.id, "Введите один логин, без пробелов")
                else:
                    if(re.match(pattern, message.text)):
                        words[0]=words[0].lower()
                        bot.send_message(message.chat.id, f"Поиск {words[0]} 🔎\n\nВаше место в очереди: {users_queue.qsize()+1}")
                        users_queue.put((message.chat.id, words, message.chat.id in premium))
                        current.append(int(message.chat.id))
                    else:
                        bot.send_message(message.chat.id, alert)
            else:
                if (len(words) > 5):
                    bot.send_message(message.chat.id, "Нельзя проверить больше 5 логинов за 1 раз")
                else:
                    f=0
                    good_words=[]
                    unique_words = []
                    seen = set()
                    for word in words:
                        lower_word = word.lower()
                        if lower_word not in seen:
                            seen.add(lower_word)
                            unique_words.append(word)
                    words = unique_words
                    for word in words:
                        word = word.lower()
                        if (not re.match(pattern, word)):
                            if(f==0):
                                bot.send_message(message.chat.id, alert)
                            f=1
                        else:
                            global premium_count
                            users_queue.queue.insert(premium_count, (message.chat.id, [word], message.chat.id in premium))
                            good_words.append(word)
                            current.append(int(message.chat.id))
                            users_queue.put((-1,[], False))
                            premium_count+=1
                    if(len(good_words)>0):
                        bot.send_message(message.chat.id, f"{"Поиск:\n"+', '.join(good_words)+' 🔎'}")
        else:
            bot.send_message(message.chat.id, f"Ваш запрос еще обрабатывается ⏱")
###

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirmation(call):
    payment_id = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup()
    payment = Payment.find_one(payment_id)
    chat_id = call.data.split("_")[2]
    text = f"""🍪 Cookie функции:

Для cookie-пользователей доступны расширенные возможности:
- Логины проходят дополнительную проверку
- Все логины в выводе гарантированно доступны
- Обработка запроса без очереди
- Вывод 25 первых логинов, вместо 10
- Возможность проверить несколько логинов одним сообщением (до 5)
- Проверка логина на доступность в других соц. сетях

Купить COOKIE навсегда за {cost} RUB 👇"""

    if payment.status == "succeeded":
        add_premium_user(chat_id)
        bot.edit_message_text(chat_id=chat_id,
                              message_id=call.message.message_id,
                              text="""Спасибо за покупку! ✅""", reply_markup=markup)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("ℹ️ Помощь"))
        bot.send_message(
            chat_id,"🍪",
            reply_markup=markup
        )
    else:
        payment_url = payment.confirmation.confirmation_url
        button1 = types.InlineKeyboardButton("Купить 💰", url=payment_url)
        button2 = types.InlineKeyboardButton("Подтвердить покупку ❌",
                                             callback_data=f"confirm_{payment_id}_{chat_id}")
        markup.add(button1)
        markup.add(button2)
        current_text = call.message.reply_markup.keyboard[1][0].text
        if(current_text!=button2.text):
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=call.message.message_id,
                                  text=text, reply_markup=markup)

loop = asyncio.new_event_loop()
thread = Thread(target=start_async_loop, args=(loop,), daemon=True)
thread.start()

bot.polling(none_stop=True)