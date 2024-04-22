import datetime
import schedule
import time


from database.db_requests import db, reminders, reminders_to_del
import telebot
import json
from tg_bot.tg_keyboards import notification_keyb

with open('config.json', 'r') as file:
    config = json.load(file)
    token = config["token"]
bot = telebot.TeleBot(token)


class Reminder:
    def __init__(self, task_id, chat_id, name, start, notify_start, end, notify_end, repeat=0):
        self.task_id = task_id
        self.chat_id = chat_id
        self.name = name
        self.start = start
        self.notify_start = notify_start
        self.end = end
        self.notify_end = notify_end
        self.repeat = repeat
        self.is_send = False


def add_del_reminders():
    closest_reminders = db.get_tasks_with_remind()
    for r in closest_reminders:
        if r[0] not in reminders and r[0] not in reminders_to_del:
            reminders[r[0]] = Reminder(*r)

    for r in reminders_to_del:
        if r in reminders:
            reminders.pop(r)
        reminders_to_del.remove(r)


def handle_reminders():
    now = datetime.datetime.now().timestamp()
    for task_id, r in reminders.items():
        # if in next minute should be notified
        if now < r.notify_start < now+60 and not r.is_send:
            text = f'Уведомление о начале задачи\nНазвание: {r.name}\nНачало задачи:{datetime.datetime.fromtimestamp(r.start)} \n'
            if r.repeat:
                r.notify_start += r.repeat*60
                text += f'Повтор уведомления каждые:{r.repeat} минут ({round(r.repeat/60, 2)} часа(ов))'
            else:
                r.is_send = True
                reminders_to_del.append(r.task_id)
            bot.send_message(r.chat_id,
                             text,
                             reply_markup=notification_keyb(r.task_id))

        if now < r.notify_end < now + 60 and not r.is_send:
            text = f'Уведомление о конце задачи\nНазвание: {r.name}\nКонц задачи:{datetime.datetime.fromtimestamp(r.end)} \n'
            if r.repeat:
                r.notify_start += r.repeat*60
                text += f'Повтор уведомления каждые:{r.repeat} минут ({round(r.repeat/60, 2)} часа(ов))'
            else:
                r.is_send = True
                reminders_to_del.append(r.task_id)
            bot.send_message(r.chat_id,
                             text,
                             reply_markup=notification_keyb(r.task_id))


schedule.every(5).minutes.do(add_del_reminders)
schedule.every(30).seconds.do(handle_reminders)

add_del_reminders()
handle_reminders()
while True:
    schedule.run_pending()
    time.sleep(1)
