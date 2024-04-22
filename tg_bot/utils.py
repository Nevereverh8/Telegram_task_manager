import datetime

from database.db_requests import sessions
import telebot
import json
from tg_bot.tg_keyboards import *
import csv

with open('config.json', 'r') as file:
    config = json.load(file)
    token = config["token"]
bot = telebot.TeleBot(token)

priority_to_emoji = {1: '🟢',
                     2: '🟡',
                     3: '🔴'}
complition_to_emoji = {0: '',
                       1: '✅'}

# classes
class User:
    def __init__(self, chat_id, bot_message, first_name='', last_name=''):
        self.chat_id = int(chat_id)
        if not db.get_item('Users', self.chat_id, by='chat_id'):
            db.create_user(self.chat_id, first_name, last_name)
        self.bot_message = bot_message
        self.task_name = ''
        self.task_cat = ''
        self.task_date_start = 0.0
        self.task_date_end = 0.0
        self.priority = 0
        self.start_remind = 0
        self.end_remind = 0
        self.repeat = 0
        self.selected_date = 0.0
        self.last_cb = 'u;menu'
        self.project_name = ''
        self.selected_project = 0
        self.users_list = []

    def reset_user(self):
        self.task_name = ''
        self.task_cat = ''
        self.task_date_start = 0.0
        self.task_date_end = 0.0
        self.priority = 0
        self.start_remind = 0
        self.end_remind = 0
        self.repeat = 0
        self.selected_date = 0.0
        self.last_cb = 'u;menu'
        self.project_name = ''
        self.selected_project = 0
        self.users_list = []

    def set_selected_project(self, id):
        self.selected_project = id

    def set_bot_message(self, message):
        self.bot_message = message

    def set_task_name(self, name):
        self.task_name = name

    def set_project_name(self, name):
        self.project_name = name

    def set_task_cat(self, cat):
        self.task_cat = cat

    def set_task_date_start(self, day):
        self.task_date_start = day

    def set_start_time(self, h, m=0):
        day = self.task_date_start
        self.task_date_start = datetime.datetime(year=day.year, month=day.month, day=day.day, hour=h, minute=m)

    def set_end_time(self, h, m=0):
        day = self.task_date_end
        self.task_date_end = datetime.datetime(year=day.year, month=day.month, day=day.day, hour=h, minute=m)

    def set_task_date_end(self, day):
        self.task_date_end = day

    def set_priority(self, level):
        self.priority = level

    def set_start_remind(self, minutes):
        self.start_remind = minutes

    def set_end_remind(self, minutes):
        self.end_remind = minutes

    def set_repeat(self, minutes):
        self.repeat = minutes

    def set_selected_date(self, day):
        if day == 'week':
            self.selected_date = 'week'
        else:
            self.selected_date = datetime.datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0)

    def set_last_cb(self, cb):
        self.last_cb = cb

    def gen_text(self):
        text = ''
        # if record:
        #     task = record
        # else:
        #     taks = (self.task_name,
        #             self.task_cat,
        #             self.task_date_start,
        #             self.task_date_end,
        #             self.priority,
        #             db.get_item('Users', self.chat_id, 'chat_id')[0][0],
        #             0,
        #             db.get_item('Projects', self.selected_project)[0][1],
        #             )
        if self.task_name:
            text += f'Задача: {self.task_name}\n'
        if self.task_cat:
            text += f"Категория: {db.get_item('Categories', self.task_cat)[0][1] }\n"
        if self.task_date_start:
            text += f"Дата и время начала: {self.task_date_start.strftime('%d.%m.%Y %H:%M')}\n"
        if self.task_date_end:
            text += f"Дата и время конца: {self.task_date_end.strftime('%d.%m.%Y %H:%M')}\n"
        return text

    def switch_user(self, user_id):
        if user_id in self.users_list:
            self.users_list.remove(user_id)
        else:
            self.users_list.append(user_id)

    def save_task(self):
        db.create_task(self.chat_id,
                       self.task_name,
                       self.task_cat,
                       self.task_date_start,
                       self.task_date_end,
                       self.priority,
                       self.start_remind,
                       self.end_remind,
                       self.repeat,
                       self.selected_project)


####################################################
# next step handlers

# handles task name input
def task_name_input(message):
    bot_message = sessions[message.chat.id].bot_message
    task_name = sessions[message.chat.id].task_name
    if message.text != task_name and sessions[message.chat.id].last_cb == 'u;menu':
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=bot_message.id,
                              text=f'Вы выбрали имя для задачи\n{message.text}',
                              reply_markup=step_keyb('u;menu', 'u;t;new;0r', 'u;t;new;1'))
        sessions[message.chat.id].set_task_name(message.text)
    elif message.text != task_name:
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=bot_message.id,
                              text=f'Вы выбрали имя для задачи\n{message.text}',
                              reply_markup=step_keyb('u;menu',
                                                     'u;t;new;0r',
                                                     'u;t;new;1'))
        sessions[message.chat.id].set_task_name(message.text)

    bot.delete_message(message.chat.id, message.id)




#################################################
# static functions
def gen_task_text(task):
    text = ''
    text += f'Задача: {task[1]} \n'
    if task[8]:
        user = db.get_item("Users", task[6])[0]
        text += f'\nПользователь: {user[2]} '
        if user[3]:
            text += user[3]
    text += f"\nКатегория: {db.get_item('Categories', task[2])[0][1]} \n"
    if task[3]:
        text += f'Начало: {datetime.datetime.fromtimestamp(task[3])} \n'
    if task[4]:
        text += f'Конец: {datetime.datetime.fromtimestamp(task[4])} \n'
    text += f'Уровень приоритета: {priority_to_emoji[task[5]]} \n'
    if task[8]:
        text += f"Проект: {db.get_item('Projects',task[8])[0][1]} \n"
    if task[9]:
        text += f'Уведомить до начала за: {task[9]} минут \n'
    if task[10]:
        text += f'Уведомить до конца за: {task[10]} минут \n'
    if task[11]:
        text += f'Повтор уведомления: раз в {task[11]} минут ({round(task[11]/60, 2)} часа(ов)) \n'
    return text


# parses call attributes for easier navigation
def call_parse(call):  # chat_id, message_id, data, text, keyb = call_parse(call)
    return call.message.chat.id, call.message.id, call.data, call.message.text, call.message.reply_markup


# for old button handle
def call_start(call, delete=True):
    chat_id, message_id, data, text, keyb = call_parse(call)
    if delete:
        bot.delete_message(chat_id, message_id)
    m = bot.send_message(chat_id,
                         'Здравствуйте, диспечтер задач к вашим услугам, чего желаете?',
                         reply_markup=main_menu_keyb)
    if chat_id not in sessions:
        sessions[chat_id] = User(chat_id, m, call.from_user.first_name, call.from_user.last_name)
        sessions[chat_id].set_bot_message(m)
    else:
        sessions[chat_id].reset_user()
        sessions[chat_id].set_bot_message(m)


def export(chat_id):
    table = db.export(chat_id)
    with open('export.csv', 'x', newline='', encoding='utf_8') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        # for row in table:
        csvwriter.writerows(table)
        file.close()
    return 'export.csv'



# def str_date_to_datetime(day):
#     day = day.split('-')
#     dt_date = datetime.datetime(year=day[0], month=day[1], day=day[2])
#     return dt_date
