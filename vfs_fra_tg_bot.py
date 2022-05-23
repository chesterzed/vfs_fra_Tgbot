import TOKEN
import telebot
import cherrypy

import os.path
import sqlite3
from telebot import types
import web_part as WP
import re

from time import sleep, time
from functools import wraps

db_name = "vfs_fra_db.sqlite"
bot = telebot.TeleBot(TOKEN.token)

##################  web hook ##################


WEBHOOK_HOST = '62.113.110.248'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = 'webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = 'webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN.token)


# Наш вебхук-сервер
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


### Декоратор для запуска функции в отдельном потоке ####


def mult_threading(func):
    @wraps(func)
    def wrapper(*args_, **kwargs_):
        import threading
        func_thread = threading.Thread(target=func,
                                       args=tuple(args_),
                                       kwargs=kwargs_)
        func_thread.start()
        return func_thread

    return wrapper


################ register user ################


@bot.message_handler(commands=['start'])  # start
def start_message(message):
    if auth_check(message):  # надо что-нибудь написать, типо  "вы вошли под аккаунтом 'почта' => меню"
        bot.send_message(message.chat.id, "Вы уже вышли в аккаунт.\nЧтобы сменить его напишите - /switch_account")
        main_menu(message)
        return
    msg = bot.send_message(message.chat.id, "Здравствуйте, введите ключ доступа для бота:")
    bot.register_next_step_handler(msg, check_security_pass)


def check_security_pass(message):
    if message.text == "1q5tFdsa0k":
        ask_uemail(message)
    else:
        bot.send_message(message.chat.id, "Неверный ключ")
        start_message(message)


def ask_uemail(message):
    msg = bot.send_message(message.chat.id, "Чтобы войти на сайт нужен аккаунт, введите почту:")
    bot.register_next_step_handler(msg, add_usr_email)


def add_usr_email(message):
    email = message.text
    ask_password(message, email)


def ask_password(message, email):
    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(msg, add_password, email=email)


def add_password(message, email):
    data = str(email) + ", " + message.text
    insert_account(message, data)


def insert_account(message, data):
    if auth_check(message):
        d = data.split(", ")
        db_update("bot_users", "email", d[0], "id", message.chat.id)
        db_update("bot_users", "password", d[1], "id", message.chat.id)
        text = "Вы успешно сменили пользователя"
    else:
        data = str(message.chat.id) + ", 0, " + data
        db_insert_bot_users(data)
        text = "Вы успешно добавили аккаунт"

    bot.send_message(message.chat.id, text)
    main_menu(message)


################## user func ###################


@bot.message_handler(commands=['switch_account'])  # switch_account (for user)
def switch_account(message):
    if not auth_check(message):
        start_message(message)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    b = types.InlineKeyboardButton(text='Отмена', callback_data='Cancel')
    markup.add(b)

    msg = bot.send_message(message.chat.id, "Введите почту:", reply_markup=markup)
    bot.register_callback_query_handler('q', back_to_menu)
    bot.register_next_step_handler(msg, add_usr_email)


################## add client ##################


@bot.message_handler(commands=['add_client'])  # add client
def start_adding_client(message):
    if not auth_check(message):
        start_message(message)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    b = types.InlineKeyboardButton(text='Отмена', callback_data='Cancel')
    markup.add(b)

    bot.send_message(message.chat.id, "l o a d i n g . . .", reply_markup=markup)
    if not os.path.exists("chfiles/VAC.txt") \
            or not os.path.exists("chfiles/AC.txt") \
            or not os.path.exists("chfiles/longSC.txt") \
            or not os.path.exists("chfiles/shortSC.txt") \
            or not os.path.exists("chfiles/genders.txt") \
            or not os.path.exists("chfiles/nationalities.txt"):
        bot.send_message(message.chat.id, "(Не все файлы прошли проверку, сейчас они будут обновлены, "
                                          "это может занять некоторое время, обычно не больше минуты)")
        reset_choice_files(message)
    bot.register_callback_query_handler('q', back_to_menu)
    ask_VAC(message)


def ask_VAC(message):
    li = []
    with open("chfiles/VAC.txt", "r") as f:
        for line in f:
            li.append(re.sub('\n', '', line))
    markup = create_button_choose_list(li)

    bot.send_message(message.chat.id, "Выберите свой визовый центр: ", reply_markup=markup)
    bot.register_next_step_handler(message, add_VAC, li=li)


def add_VAC(message, li):
    if message.text == 'Отмена':
        main_menu(message)
        return
    if message.text not in li:
        ask_VAC(message)
        return

    data = str(message.text) + ", "
    ask_AC(message, data=data)


def ask_AC(message, data):
    li = []
    with open("chfiles/AC.txt", "r") as f:
        for line in f:
            li.append(re.sub('\n', '', line))
    markup = create_button_choose_list(li)
    bot.send_message(message.chat.id, "Выберите категорию записи: ", reply_markup=markup)
    bot.register_next_step_handler(message, add_AC, li=li, data=data)


def add_AC(message, li, data):
    if message.text == 'Отмена':
        main_menu(message)
        return
    if message.text not in li:
        ask_AC(message, data)
        return

    data += str(message.text) + ", "
    ask_SC(message, data=data, answer=message.text)


def ask_SC(message, data, answer):
    li = []
    fn = ''
    if answer == 'Long Stay':
        fn = "chfiles/longSC.txt"
    elif answer == 'Short Stay':
        fn = "chfiles/shortSC.txt"
    else:
        fn = "chfiles/shortSC.txt"
    with open(fn, "r") as f:
        for line in f:
            li.append(re.sub('\n', '', line))
    markup = create_button_choose_list(li)
    bot.send_message(message.chat.id, "Выберите подкатегорию: ", reply_markup=markup)
    bot.register_next_step_handler(message, add_SC, li=li, data=data, answer=answer)


def add_SC(message, li, data, answer):
    if message.text == 'Отмена':
        main_menu(message)
        return
    if message.text not in li:
        ask_SC(message, data, answer)
        return

    data += str(message.text) + ", "
    ask_fra_visa(message, data=data)


def ask_fra_visa(message, data):
    msg = bot.send_message(message.chat.id, "Введите визу (Формат: FRAXXXAAAAYNNNNNN):")
    bot.register_next_step_handler(msg, add_fra_visa, data=data)


def add_fra_visa(message, data):
    # add to bd or to the next func (сделать заглавными буквами)
    data += re.sub('\W', '', str(message.text).upper()) + ', '
    ask_name(message, data=data)


def ask_name(message, data):  # ask name  # data: фио, телефон, номер паспорта, дата рождения
    msg = bot.send_message(message.chat.id, "Введите имя (на английском):")
    bot.register_next_step_handler(msg, add_name, data=data)


def add_name(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_surname(message, data)


def ask_surname(message, data):
    msg = bot.send_message(message.chat.id, "Введите фамилию (на английском):")
    bot.register_next_step_handler(msg, add_surname, data=data)


def add_surname(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_gender(message, data)


def ask_gender(message, data):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    with open("chfiles/genders.txt", "r+") as file:
        for i in file:
            markup.add(types.InlineKeyboardButton(i))
    msg = bot.send_message(message.chat.id, "Выберите пол:", reply_markup=markup)
    bot.register_next_step_handler(msg, add_gender, data=data)


def add_gender(message, data):
    data += message.text + ", "
    ask_birth(message, data)


def ask_birth(message, data):
    msg = bot.send_message(message.chat.id, "Введите дату рождения (в таком формате ddmmyyyy, "
                                            "\nнапример 20/05/1998 => 20051998):")
    bot.register_next_step_handler(msg, add_birth, data=data)


def add_birth(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_nationality(message, data)


def ask_nationality(message, data):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    with open("chfiles/nationalities.txt", "r+") as file:
        for i in file:
            markup.add(types.InlineKeyboardButton(i))
    msg = bot.send_message(message.chat.id, "Выберите гражданство:", reply_markup=markup)
    bot.register_next_step_handler(msg, add_nationality, data=data)


def add_nationality(message, data):
    data += message.text + ", "
    ask_passport_num(message, data)


def ask_passport_num(message, data):
    msg = bot.send_message(message.chat.id, "Введите номер паспорта:")
    bot.register_next_step_handler(msg, add_passport_num, data=data)


def add_passport_num(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_passport_expiry(message, data)


def ask_passport_expiry(message, data):
    msg = bot.send_message(message.chat.id, "Введите срок действия поспорта (в таком формате ddmmyyyy, "
                                            "\nнапример 20/05/2018 => 20052018):")
    bot.register_next_step_handler(msg, add_passport_expiry, data=data)


def add_passport_expiry(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_country_code(message, data)


def ask_country_code(message, data):
    msg = bot.send_message(message.chat.id, "Введите код страны (первые цифры в телефонном номере\nнапример 44):")
    bot.register_next_step_handler(msg, add_country_code, data=data)


def add_country_code(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_phone_number(message, data)


def ask_phone_number(message, data):
    msg = bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(msg, add_phone_number, data=data)


def add_phone_number(message, data):
    data += re.sub('\W', '', message.text) + ", "
    ask_email(message, data)


def ask_email(message, data):
    msg = bot.send_message(message.chat.id, "Введите электронный адрес:")
    bot.register_next_step_handler(msg, add_email, data=data)


def add_email(message, data):
    data += message.text
    db_insert_queue(data)

    bot.send_message(message.chat.id, "Вы успешно добавили клиента")
    main_menu(message)


#################### queue ####################

@bot.message_handler(commands=['show_queue'])
def show_queue(message):
    if not auth_check(message):
        start_message(message)
        return

    text = ''
    sel = db_select_all("*", "queue")
    if sel:
        for i in sel:
            text += list_to_line_text(i)
            text += '\n\n'
    else:
        text = "Сейчас никого в очереди нет."
    bot.send_message(message.chat.id, text)
    if message.text == "/show_queue":
        main_menu(message)


@bot.message_handler(commands=['delete_from_queue'])
def delete_from_queue(message):
    if not auth_check(message):
        start_message(message)
        return

    show_queue(message)
    msg = bot.send_message(message.chat.id, "Введите номер клиента, которого хотите удалить\n(0 - для отмены):")
    bot.register_next_step_handler(msg, delete_one_client)


def delete_one_client(message):
    try:
        db_delete("queue", "id", message.text)
    except:
        bot.send_message(message.chat.id, "Нет такого номера клиента(цифра сверху)")
    main_menu(message)


def list_to_line_text(li):
    text = ''
    for line in li:
        text += str(line) + '\n'
    return text


################# server part #################


def open_browser():
    driver = WP.open_browser_and_website()
    return driver


def login(driver):
    # убрать 0, если заказчик попросит
    data = db_select_all("*", "bot_users")
    email = data[0][2]
    pw = data[0][3]

    WP.account_enter(driver, email, pw)


def enter_search_params(driver, data):
    # set args
    WP.start_new_booking(driver)

    li = WP.show_VAC(driver)
    WP.choose_VAC(driver, len(li), data[1])
    li = WP.show_AC(driver)
    WP.choose_AC(driver, len(li), data[2])
    li = WP.show_SC(driver)
    WP.choose_SC(driver, len(li), data[3])
    if WP.check_alert(driver, False, "//div[text()=' В настоящее время нет свободных мест для записи ']"):
        return False
    WP.next_step_to_ur_det(driver)
    return True


def enter_other_details(driver, data):
    WP.set_your_details(driver, data)
    if WP.check_alert(driver, True, "//button[contains(@class,'mat-focus-indicator btn')]"):
        return
    WP.next_to_date(driver)
    WP.set_date(driver)
    WP.last_confirm(driver)


################# check client #################


def check_client_func(driver, data):  # arg == client data
    try:
        if not enter_search_params(driver, data):
            return True
    except:
        send_app_to_everyone("Ошибка подключения, постоянная проверка ненадолго приостановлена")
        send_app_to_everyone("Добавление клиентов всё ещё работает!")
        driver.close()
        sleep(1800)
        return False
    try:
        enter_other_details(driver, data)
        db_delete("queue", "id", data[0])
        text = list_to_line_text(data)
        send_app_to_everyone("Успешно записан клиент из очереди:\n" + text)  # добавить время и дату записи в сообщение
    except:
        text = list_to_line_text(data)
        send_app_to_everyone("Ошибка подключения или клиента неверно введены данные:\n" + text)
    return True


@mult_threading
def check_all_queue():
    while True:
        db_list = db_select_all("*", "queue")
        count = len(db_list)
        if count != 0:
            driver = open_browser()
            login(driver)
            for i in db_list:
                if not check_client_func(driver, i):
                    return
                WP.wait_load(driver, 15, "ngx-overlay")
            driver.close()
        sleep(1800)


################ help functions ################


def db_connect():
    return sqlite3.connect(db_name)


def db_select_one(s_what, s_list, s_where, s_what_where):
    con = db_connect()
    curs = db_connect().cursor()
    curs.execute("SELECT " + s_what + " FROM " + s_list + " WHERE " + s_where + " = ?", (s_what_where,))
    selected = curs.fetchone()
    con.close()
    return selected


def db_select_all(s_what, s_list):
    con = db_connect()
    curs = db_connect().cursor()
    curs.execute("SELECT " + s_what + " FROM " + s_list)
    selected = curs.fetchall()
    con.close()
    return selected


def db_update(u_list, u_what, u_set, where, u_what_where):
    con = db_connect()
    curs = con.cursor()
    curs.execute("UPDATE " + u_list + " SET " + u_what + " = ? WHERE " + where + " = ?", (u_set, u_what_where,))
    con.commit()
    con.close()


def db_insert(col_names_list, col_values_list, table_name):
    l1 = ""
    qq = ""
    con = db_connect()
    curs = con.cursor()
    for i in col_names_list:
        l1 += str(i) + ","
        qq += "?,"
    l1 = ','.join(l1.split(',')[:-1])
    qq = ','.join(qq.split(',')[:-1])

    curs.execute(f"INSERT INTO " + table_name + " (" + l1 + ") VALUES (" + qq + ")", col_values_list.split(", "))
    con.commit()
    con.close()


def db_insert_bot_users(data):  # idInTable=0, isOnline=0, email='', password=''
    names_list = ["id", "isOnline", "email", "password"]
    db_insert(names_list, data, "bot_users")


def db_insert_queue(data):
    names_list = ["VAC", "AC", "SC", "FRA", "name", "surname", "gender", "dateOfBirth", "nationality",
                  "ppNumber", "ppExpiryDate", "phoneCode", "phoneNumber", "email"]
    db_insert(names_list, data, "queue")


def db_delete(d_list, where, d_where):
    con = db_connect()
    curs = con.cursor()
    curs.execute("DELETE FROM " + d_list + " WHERE " + where + " = ?", (d_where,))
    con.commit()
    con.close()


def auth_check(message):
    usr_id = db_select_one("id", "bot_users", "id", message.chat.id)
    if usr_id != 'None' and usr_id is not None:
        return True
    else:
        return False


def clear_handlers(message):
    bot.clear_step_handler(message)
    bot.clear_reply_handlers(message)
    bot.callback_query_handlers.clear()


def create_button_choose_list(li):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.InlineKeyboardButton('Отмена'))
    for i in li:
        markup.add(types.InlineKeyboardButton(i))
    return markup


def send_app_to_everyone(text):
    id_list = db_select_all("id", "bot_users")
    for i in id_list:
        bot.send_message(i[0], text)


@bot.message_handler(commands=['reset'])
def reset_choice_files(message):
    if not auth_check(message):
        start_message(message)
        return
    try:
        send_app_to_everyone("l o a d i n g . . .\n(~ 1 min)")
        WP.reset_all_choice_files()
        send_app_to_everyone("success !")
    except:
        send_app_to_everyone("failed reset, but it's working")


################## main menu ###################


@bot.message_handler(commands=['menu'])  # main menu
def main_menu(message):
    if not auth_check(message):
        start_message(message)
        return

    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Меню"
                                      "\nНажмите:"
                                      "\n/add_client - для добавления клиента в очередь"
                                      "\n/show_queue - для просмотра очереди клиентов"
                                      "\n/delete_from_queue - для удаления клиента из очереди"
                                      "\n\n/switch_account - для смены вашего логина и пароля"
                                      "\n\n/menu - меню",
                     reply_markup=markup)


def back_to_menu(smth):
    clear_handlers(smth.message)
    main_menu(smth.message)


################# main handler #################


@bot.message_handler(content_types=['text'])  # text
def text_handler(message):
    clear_handlers(message)
    if not auth_check(message):
        start_message(message)
        return

    if message.text == "Добавить клиента":
        start_adding_client(message)
    elif message.text == "Сменить аккаунт":
        switch_account(message)


################################################

# try:
#     send_app_to_everyone("l o a d i n g . . .\n(~ 1 min)")
#     WP.reset_all_choice_files()
#     send_app_to_everyone("success !")
# except:
#     pass
# send_app_to_everyone("/menu - чтобы показать меню")

# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
bot.remove_webhook()

# Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

# Собственно, запуск!
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

check_all_queue()

bot.polling(none_stop=True, timeout=999999)
