import telebot
import json
import datetime
import os
from database.db_requests import sessions, reminders, reminders_to_del, db
from telebot.types import ReplyKeyboardRemove, CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from tg_bot.tg_keyboards import *
from tg_bot.utils import *


ru_step = {'year': 'год',
           'month': 'месяц',
           'day': 'день'
            }


# next_step_hanlders
# handles project name input
def project_name_input(message):
    bot_message = sessions[message.chat.id].bot_message
    project_name = sessions[message.chat.id].project_name
    if message.text != project_name and message.text not in [project[1] for project in db.get_projects_list(message.chat.id)]:
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=bot_message.id,
                              text=f'Вы выбрали имя для проекта\n{message.text}',
                              reply_markup=step_keyb('u;menu', 'p;new', 'p;new;1'))
        sessions[message.chat.id].set_project_name(message.text)
    elif message.text in [project[1] for project in db.get_projects_list(message.chat.id)]:
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=bot_message.id,
                              text=f'У вас уже есть проект с таким именем, выберите другое имя')
        bot.register_next_step_handler(message, project_name_input)
    bot.delete_message(message.chat.id, message.id)


with open('config.json', 'r') as file:
    config = json.load(file)
    token = config["token"]
    bot_link = config["bot_link"]
bot = telebot.TeleBot(token)

@bot.channel_post_handler(func=lambda message: message.text.startswith('/connect'))
def connect_channel_to_project(message):
    if not db.get_item('Projects', message.chat.id, 'channel_id'):
        if len(message.text.split('_')) == 3:
            if message.text.split('_')[1].isdigit() and message.text.split('_')[2].isdigit():
                proj_id = int(message.text.split('_')[1])
                proj = db.get_item('Projects', proj_id)
                if not proj[0][3] and int(message.text.split('_')[2]) == proj[0][2]:
                    db.update_cell('Projects', proj_id, 'channel_id', message.chat.id)
                    bot.send_message(message.chat.id,
                                     f'Канал успешно подключен к проекту {proj[0][1]} \nСсылка для присоединения к проекту {bot_link}?start=join_{proj[0][0]} (пройти и нажать старт)')
    bot.delete_message(message.chat.id,
                       message.id)




@bot.message_handler(commands=['start', 'help'])
def commands_handler(message):
    chat_id = message.chat.id
    if message.text == '/start':
        bot.delete_message(chat_id, message_id=message.id)
        m = bot.send_message(chat_id,
                             'Здравствуйте, диспечтер задач к вашим услугам, чего желаете?',
                             reply_markup=main_menu_keyb)
        if chat_id not in sessions:
            sessions[chat_id] = User(chat_id, m, message.from_user.first_name, message.from_user.last_name)
        else:
            sessions[chat_id].set_bot_message(m)
    elif message.text.split('_')[0] == '/start join':
        if chat_id not in sessions:
            sessions[chat_id] = User(chat_id, message, message.from_user.first_name, message.from_user.last_name)
        db.join_project(int(message.text.split('_')[1]), message.chat.id)
        bot.delete_message(chat_id,
                           message.id)
        m = bot.send_message(chat_id,
                             f"Вы успешно подключились к проекту {db.get_item('Projects', int(message.text.split('_')[1]))[0][1]}",
                             reply_markup=slider('do-nothing', [], menu_callback_data='u;menu'))
        sessions[chat_id].set_bot_message(m)


# step2: calendars and time handlers

# start cal
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal1(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id, message_id, data, text, keyb = call_parse(call)
    result, key, step = DetailedTelegramCalendar(calendar_id=1,
                                                 locale='ru',
                                                 min_date=datetime.date.today()).process(data)
    if not result and key:
        bot.edit_message_text(f"Выберите {ru_step[LSTEP[step]]}",
                              chat_id,
                              message_id,
                              reply_markup=key)
    elif result:
        sessions[chat_id].set_task_date_start(result)
        if sessions[chat_id].last_cb != 'u;menu':
            bot.edit_message_text(sessions[chat_id].gen_text()+'\nВыберите время качала задачи',
                                  chat_id,
                                  message_id,
                                  reply_markup=time_keyb(sessions[chat_id].last_cb))
        else:
            bot.edit_message_text(sessions[chat_id].gen_text(),
                                  chat_id,
                                  message_id,
                                  reply_markup=step_keyb('u;menu', 'u;t;new;3;s;y', 'u;t;new;3;s;t'))


# end cal
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal2(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id, message_id, data, text, keyb = call_parse(call)
    result, key, step = DetailedTelegramCalendar(calendar_id=2,
                                                 locale='ru',
                                                 min_date=datetime.date.today()
                                                 ).process(data)
    if not result and key:
        bot.edit_message_text(f"Выберите {ru_step[LSTEP[step]]}",
                              chat_id,
                              message_id,
                              reply_markup=key)

    elif result:
        sessions[chat_id].set_task_date_end(result)
        if sessions[chat_id].last_cb != 'u;menu':
            bot.edit_message_text(sessions[chat_id].gen_text()+'\nВыберите время конца задачи',
                                  chat_id,
                                  message_id,
                                  reply_markup=time_keyb(sessions[chat_id].last_cb))
        else:
            bot.edit_message_text(sessions[chat_id].gen_text(),
                                  chat_id,
                                  message_id,
                                  reply_markup=step_keyb('u;menu', 'u;t;new;3;e;y', 'u;t;new;3;e;t'))


# show cal
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=3))
def cal3(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id, message_id, data, text, keyb = call_parse(call)
    result, key, step = DetailedTelegramCalendar(calendar_id=3,
                                                 locale='ru').process(data)
    if not result and key:
        bot.edit_message_text(f"Выберите {ru_step[LSTEP[step]]}",
                              chat_id,
                              message_id,
                              reply_markup=key)
    elif result:
        sessions[chat_id].set_selected_date(result)
        bot.edit_message_text(chat_id=chat_id,
                              message_id=message_id,
                              text=f'Какие задачи на {result} хотите просмотреть?',
                              reply_markup=task_types_keyb('u;t;date;day'))


# basic callback
@bot.callback_query_handler(func=lambda call: True)
def callback_handlle(call):

    print(f'call data: {call.data} ---------time:{datetime.datetime.now()}')
    chat_id, message_id, data, text, keyb = call_parse(call)
    data = data.split(';')
    # for old button handle                                     # here is some scary shit happens, need more tests
    if len(data) > 3:
        if chat_id not in sessions:
            if data[2] in ['fin', 'n']:
                sessions[chat_id] = User(chat_id, call.message, call.from_user.first_name, call.from_user.last_name)
                if data[3] == 'close':
                    bot.delete_message(chat_id, message_id)
                    return
            else:
                bot.answer_callback_query(call.id)
                call_start(call)
                return

    if chat_id not in sessions:
        call_start(call)
        return

    elif not sessions[chat_id].bot_message:
        call_start(call)
    # MESSAGE BOXES finished creating task or task
    if len(data) == 5:
        if data[3] == '5' and data[0] == 'u' and not sessions[chat_id].selected_project:
            bot.answer_callback_query(call.id, 'Задача записана')  # finish of creating task
        elif data[2] in ['fin', 'del'] and data[-1] == 'y':
            bot.answer_callback_query(call.id, 'Задача завершена')  # finishing existiтg task
        else:
            bot.answer_callback_query(call.id)
    elif call.data == 'p;new;1':
        bot.answer_callback_query(call.id, f'Проект {sessions[chat_id].project_name} создан', )  # created project
    else:
        bot.answer_callback_query(call.id)
    # user part
    if data[0] == 'u':
        if data[1] == 'menu':
            sessions[chat_id].reset_user()
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=sessions[chat_id].bot_message.id,
                                  text='Здравствуйте, диспечтер задач к вашим услугам, чего желаете?',
                                  reply_markup=main_menu_keyb)

        # tasks
        elif data[1] == 't':
            # task menu
            if len(data) == 2:
                user_tasks = db.get_users_tasks(chat_id)
                if user_tasks:
                    bot.edit_message_text(chat_id=chat_id,
                                          message_id=sessions[chat_id].bot_message.id,
                                          text='Ваши задачи',
                                          reply_markup=task_keyb)
                else:
                    bot.edit_message_text(chat_id=chat_id,
                                          message_id=sessions[chat_id].bot_message.id,
                                          text='На данный момент у вас нет ни одной задачи, хотите создать задачу?',
                                          reply_markup=no_task_keyb)

            elif data[2] == 'all':
                print('yep')
                if data[-2] == 'm':
                    page = int(data[-1])
                else:
                    page = 0
                tasks = db.get_users_tasks(chat_id, sessions[chat_id].selected_date)
                if tasks:
                    text = f"Ваши задачи "
                    tasks = [(i[1] + priority_to_emoji[i[5]], i[0]) for i in tasks]
                else:
                    text = f"У вас нет задач"
                sessions[chat_id].set_last_cb(f'u;t;{data[2]}')
                bot.edit_message_text(chat_id=chat_id,
                                      message_id=message_id,
                                      text=text + '\n',
                                      reply_markup=slider(f'u;t;{data[2]}', tasks, page, row_num=5,
                                                          itemprefix='u;t;show',
                                                          menu_callback_data='u;menu'))
            else:
                # new task
                if data[2] == 'new':
                    # step 0 reset name
                    if data[3] == '0r':
                        sessions[chat_id].set_task_name('')
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text='Введите имя для задачи')
                        bot.register_next_step_handler(call.message, task_name_input)
                    # step 0 edit name
                    elif data[3] == '0':
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=f'Вы выбрали имя для задачи\n{sessions[chat_id].task_name}',
                                              reply_markup=step_keyb('u;menu', 'u;t;new;0r', 'u;t;new;1'))
                    # step 1
                    elif data[3] == '1':
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=sessions[chat_id].gen_text()+'Введите категорию задачи',
                                              reply_markup=cat_keyb('u;t;new;2'))
                    # step 2
                    elif data[3] == '2':
                        sessions[chat_id].set_task_cat(int(data[4]))  # cat id
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=sessions[chat_id].gen_text()+'Хотите установить дату начала задачи?',
                                              reply_markup=keybool('u;t;new;3;s'))
                    # step 3 date and time
                    elif data[3] == '3':
                        # start
                        if data[4] == 's':
                            # start date
                            if data[5] == 'y':
                                sessions[chat_id].set_last_cb('u;menu')
                                sessions[chat_id].task_date_start = 0.0
                                calendar1, step = DetailedTelegramCalendar(calendar_id=1,
                                                                           min_date=datetime.date.today(),
                                                                           locale='ru').build()
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Выберите дату',
                                                      reply_markup=calendar1)
                            # to end date
                            elif data[5] == 'n' or ((data[-1] == 'n' or data[-1].isdigit()) and data[-2] == 't'):
                                if len(data) == 7:
                                    if data[6].isdigit():
                                        sessions[chat_id].set_start_time(int(data[6]))
                                    else:
                                        sessions[chat_id].set_start_time(0)
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text=sessions[chat_id].gen_text() + 'Хотите установить дату конца задачи?',
                                                      reply_markup=keybool('u;t;new;3;e'))
                            # start time ?
                            elif data[5] == 't':
                                if len(data) == 6:
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text='Хотите установить время начала задачи?',
                                                          reply_markup=keybool('u;t;new;3;s;t'))
                                # time start
                                elif data[6] == 'y':
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text='Выберите время начала задачи',
                                                          reply_markup=time_keyb('u;t;new;3;s;t'))

                        # end
                        elif data[4] == 'e':
                            # end date
                            if data[5] == 'y':
                                sessions[chat_id].set_last_cb('u;menu')
                                sessions[chat_id].task_date_end = 0.0
                                calendar2, step = DetailedTelegramCalendar(calendar_id=2,
                                                                           min_date=datetime.date.today(),
                                                                           locale='ru').build()
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Выберите дату',
                                                      reply_markup=calendar2)
                            # to reminders
                            elif data[5] == 'n' or ((data[-1] == 'n' or data[-1].isdigit()) and data[-2] == 't'):  # 5-n
                                if len(data) == 7:
                                    if data[6].isdigit():
                                        sessions[chat_id].set_end_time(int(data[6]))
                                    else:
                                        sessions[chat_id].set_end_time(0)
                                if sessions[chat_id].task_date_start or sessions[chat_id].task_date_end:
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text=sessions[chat_id].gen_text()+'Хотите установить уведомления к этой задаче?',
                                                          reply_markup=keybool('u;t;new;4'))
                                else:
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text='Установите задаче приоритет',
                                                          reply_markup=priority_keyb('u;t;new;5'))
                            # end time ?
                            elif data[5] == 't':
                                if len(data) == 6:
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text='Хотите установить время конца задачи?',
                                                          reply_markup=keybool('u;t;new;3;e;t'))
                                # time end
                                elif data[6] == 'y':
                                    bot.edit_message_text(chat_id=chat_id,
                                                          message_id=message_id,
                                                          text='Выберите время конца задачи',
                                                          reply_markup=time_keyb('u;t;new;3;e;t'))
                    # step 4 reminders
                    elif data[3] == '4':
                        if data[4] == 'y':
                            if sessions[chat_id].task_date_start:
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Когда вам напомнить о начале задачи?',
                                                      reply_markup=reminder_keyb('u;t;new;4;s'))
                            else:
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Когда вам напомнить о конце задачи?',
                                                      reply_markup=reminder_keyb('u;t;new;4;e'))
                        # no reminders
                        elif data[4] == 'n':
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='Установите задаче приоритет',
                                                  reply_markup=priority_keyb('u;t;new;5'))
                        # start reminder
                        elif data[4] == 's':
                            # set reminder
                            if data[5] != 'n':
                                sessions[chat_id].set_start_remind(int(data[5]))
                            # propose end reminder if it has date
                            if sessions[chat_id].task_date_end:
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Хорошо, а об окончании задачи напомнить?',
                                                      reply_markup=reminder_keyb('u;t;new;4;e'))
                            # repeat interval proposal
                            else:
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='Выберите интервал для повтора уведомлений',
                                                      reply_markup=repeat_keyb('u;t;new;4;r'))
                        # end reminder
                        elif data[4] == 'e':
                            # set end reminder
                            if data[5] != 'n':
                                sessions[chat_id].set_end_remind(int(data[5]))
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='Выберите интервал для повтора уведомлений',
                                                  reply_markup=repeat_keyb('u;t;new;4;r'))
                        # repeat
                        elif data[4] == 'r':
                            # set repeat
                            if data[5] != 'n':
                                sessions[chat_id].set_repeat(int(data[5]))
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='Установите задаче приоритет',
                                                  reply_markup=priority_keyb('u;t;new;5'))

                    # step 5 priority
                    elif data[3] == '5':
                        if data[4].isdigit():
                            sessions[chat_id].set_priority(int(data[4]))
                        if data[-1] == 'save':
                            if sessions[chat_id].users_list:
                                proj_participants = db.get_project_users(sessions[chat_id].selected_project)
                                proj = db.get_item('Projects', sessions[chat_id].selected_project)[0]
                                proj_name, proj_channel = proj[1], proj[3]
                                for user in proj_participants:
                                    if user[0] in sessions[chat_id].users_list:
                                        task_id = db.create_task(user[1],
                                                                 sessions[chat_id].task_name,
                                                                 sessions[chat_id].task_cat,
                                                                 sessions[chat_id].task_date_start,
                                                                 sessions[chat_id].task_date_end,
                                                                 sessions[chat_id].priority,
                                                                 sessions[chat_id].start_remind,
                                                                 sessions[chat_id].end_remind,
                                                                 sessions[chat_id].repeat,
                                                                 sessions[chat_id].selected_project)
                                        bot.send_message(chat_id=user[1],
                                                         text=f'Вам назначена задача: \n'+gen_task_text(db.get_item('Tasks', task_id[0])[0]),
                                                         reply_markup=notification_keyb(task_id, is_assignment=True))
                                if len(sessions[chat_id].users_list) > 1:
                                    task = db.get_item('Tasks', task_id[0])
                                    text = f'Задача: \n' + task[0][1]
                                    if task[0][4]:
                                        text += f"\nОкончание:\n{datetime.datetime.fromtimestamp(task[0][4])}')"
                                    bot.send_message(
                                        chat_id=db.get_item('Projects', sessions[chat_id].selected_project)[0][3],
                                        text=text)
                                bot.edit_message_text(chat_id=chat_id,
                                                      message_id=message_id,
                                                      text='задача проекта поставлена')
                                call_start(call)
                        elif sessions[chat_id].selected_project:
                            if len(data) == 5:
                                page = 0
                            elif data[-2] == 'm':
                                page = data[-1]
                            elif data[-2] == 'su':
                                sessions[chat_id].switch_user(int(data[-1]))
                            proj_participants = [(user[2] + f' {user[3]}'.replace('None', ''), user[0])for user in db.get_project_users(sessions[chat_id].selected_project)]
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='Выберите людей ответственных за выполнение этой задачи (это обязательно)\nОтветственные:\n'+'\n'.join(
                                                      [user[0] for user in proj_participants if user[1] in sessions[chat_id].users_list]),
                                                  reply_markup=slider(prefix='u;t;new;5',
                                                                      listy=proj_participants,
                                                                      itemprefix='u;t;new;5;su',
                                                                      menu_callback_data='u;menu'))
                        else:
                            sessions[chat_id].save_task()
                            sessions[chat_id].reset_user()
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='Здравствуйте, диспечтер задач к вашим услугам, чего желаете?',
                                                  reply_markup=main_menu_keyb)

                # show day tasks
                elif data[2] == 'date':
                    if data[-1] == 'cal':
                        calendar3, step = DetailedTelegramCalendar(calendar_id=3,
                                                                   locale='ru').build()
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text='Выберите дату',
                                              reply_markup=calendar3)
                    # today types
                    elif data[-1] == 'now':
                        sessions[chat_id].set_selected_date(datetime.datetime.now())
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text='Какие задачи хотите просмотреть?',
                                              reply_markup=task_types_keyb(f'u;t;date;{data[3]}'))
                    elif data[-1] == 'week':
                        sessions[chat_id].set_selected_date('week')
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text='Какие задачи хотите просмотреть?',
                                              reply_markup=task_types_keyb(f'u;t;date;{data[3]}'))
                    # show tasks that starts/ends/active on date
                    elif len(data) == 5 or len(data)>5 and data[-2] == 'm':       # slider start and move between pages   #!!!!!!!!!!!!!!!!!!! test slider
                        if data[-2] == 'm':
                            page = int(data[-1])
                        else:
                            page = 0
                        if sessions[chat_id].selected_date == 'week':
                            now = datetime.datetime.now()
                            date_1 = datetime.datetime(now.year, now.month, now.day)
                            date_2 = date_1 + datetime.timedelta(days=7)
                            tasks = db.get_users_tasks(chat_id, date_1, date_2, condition=data[4])
                        else:
                            tasks = db.get_users_tasks(chat_id, sessions[chat_id].selected_date, condition=data[4])
                        if tasks:
                            if sessions[chat_id].selected_date =='week':
                                text = f"Задачи на 7 дней"
                            else:
                                text = f"Задачи на {sessions[chat_id].selected_date.strftime('%d.%m.%Y')}"
                            tasks = [(i[1]+priority_to_emoji[i[5]], i[0]) for i in tasks]
                        else:
                            if sessions[chat_id].selected_date == 'week':
                                text = f"У вас нет задач на ближайшие 7 дней по данному условию"
                            else:
                                text = f"У вас нет задач на {sessions[chat_id].selected_date.strftime('%d.%m.%Y')} по данному условию"
                        sessions[chat_id].set_last_cb(f'u;t;date;{data[3]};{data[4]}')
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=text+'\n',
                                              reply_markup=slider(f'u;t;date;{data[3]};{data[4]}', tasks, page, row_num=5,
                                                                  itemprefix='u;t;show',
                                                                  menu_callback_data='u;menu'))

                # show selected task
                elif data[2] == 'show':       # btn click in slider
                    task = db.get_item('Tasks', int(data[3]))[0]
                    text = gen_task_text(task)
                    bot.edit_message_text(chat_id=chat_id,
                                          message_id=message_id,
                                          text=text,
                                          reply_markup=show_keyb(sessions[chat_id].last_cb, task[0]))
                # finish task
                elif data[2] == 'fin' and data[-1] not in ['y', 'n']:
                    task = db.get_item('Tasks', int(data[3]))
                    if task:
                        task = task[0]
                    else:
                        bot.delete_message(chat_id, message_id)
                        return

                    # if project related task
                    if task[8] and not task[7]:
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=text,
                                              reply_markup=keybool(f'u;t;fin;{data[3]}'))

                    # if personal task
                    else:
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text=text+'\nУверены что хотите завершить эту задачу?',
                                              reply_markup=keybool(f'u;t;del;{data[3]}'))
                # finish/del confirm
                elif data[2] in ['fin', 'del'] and data[-1] in ['y', 'n']:
                    # if task finished go back to previous task list
                    if data[-1] == 'y':
                        if data[2] == 'fin':
                            if int(data[-2]) in reminders:
                                reminders[int(data[-2])].is_send = True
                                reminders_to_del.append(reminders[int(data[-2])].task_id)
                            db.update_cell('Tasks', int(data[-2]), 'is_finished', 1)
                        elif data[2] == 'del':
                            if int(data[-2]) in reminders:
                                reminders[int(data[-2])].is_send = True
                                reminders_to_del.append(reminders[int(data[-2])].task_id)
                            db.del_item('Tasks', int(data[-2]))
                        if sessions[chat_id].last_cb[0] == 'p':
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text='задача завершена',
                                                  reply_markup=slider(',',[], menu_callback_data='u;menu'))
                        elif sessions[chat_id].last_cb != 'u;menu':
                            tasks = db.get_users_tasks(chat_id, sessions[chat_id].selected_date, condition=sessions[chat_id].last_cb.split(';')[4])
                            if tasks:
                                text = f"Задачи на {sessions[chat_id].selected_date.strftime('%d.%m.%Y')}"
                                tasks = [(i[1]+f' {priority_to_emoji[i[5]]}', i[0]) for i in tasks]
                                keyb = slider(f'{sessions[chat_id].last_cb}', tasks,
                                              row_num=5,
                                              itemprefix='u;t;show',
                                              menu_callback_data='u;menu')
                            else:
                                text = f"У вас нет задач на {sessions[chat_id].selected_date.strftime('%d.%m.%Y')} по данному условию"
                                keyb = slider(',',[], menu_callback_data='u;menu')
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=message_id,
                                                  text=text + '\n',
                                                  reply_markup=keyb)
                        else:
                            # place where u get after finishing task in notification, and seems like this inly deletes task, no option for finish yet
                            if int(data[-2]) in reminders:
                                reminders[int(data[-2])].is_send = True
                                reminders_to_del.append(reminders[int(data[-2])].task_id)
                            bot.delete_message(chat_id, message_id)
                    # if task not finished, go back to it
                    else:
                        keyb = sessions[chat_id].bot_message.reply_markup
                        task = db.get_item('Tasks', int(data[-2]))[0]
                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=message_id,
                                              text='\n'.join(text.split('\n')[:-1]),
                                              reply_markup=keyb)
                                              #reply_markup=show_keyb(sessions[chat_id].last_tasks_cb, task[0]))
                # notification
                elif data[2] == 'n':
                    # repeat off
                    if data[3:5] == ['r', 'off']:
                        if int(data[5]) in reminders:
                            reminders[int(data[5])].is_send = True
                            reminders_to_del.append(reminders[int(data[5])].task_id)
                        else:
                            bot.delete_message(chat_id, message_id)
                            return
                        keyb.keyboard.pop(1)
                        bot.edit_message_text('\n'.join(text.split('\n')[:-1])+'\nПовтор выключен', chat_id,message_id,reply_markup=keyb)
                    elif data[3] == 'close':
                        bot.delete_message(chat_id, message_id)
                        return
                # task change
                elif data[2] == 'change':
                    task = db.get_item('Tasks', int(data[3]))
                    if task:
                        task = task[0]
                        text = gen_task_text(task)
                        if len(data) == 4:
                            text += f'\n\nВыберите что вы хотите изменить в задаче'
                            keyb = change_task_keyb(call.data, is_owned=True)
                            if task[8]:
                                proj = db.get_item('Projects', task[8])[0]
                                if db.get_item('Users',  chat_id, 'chat_id')[0][0] != proj[2]:
                                    keyb = change_task_keyb(call.data)
                            sessions[chat_id].last_cb = call.data
                        elif data[4] == 'name':
                            if data[-1] == 'name':
                                text = 'Выберите новое имя для задачи'
                                keyb = None
                                bot.register_next_step_handler(call.message, task_name_input)
                                sessions[chat_id].set_last_cb(call.data)
                            elif data[-1] == 'y':
                                db.update_cell('Tasks', int(data[3]), 'name', sessions[chat_id].task_name)
                                task = db.get_item('Tasks', int(data[3]))  #
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                                sessions[chat_id].set_last_cb(';'.join(data[:4]))
                        elif data[4] == 'prior':
                            if data[-1] == 'prior':
                                text = f'Выберите уровень приоритета'
                                keyb = priority_keyb(call.data)
                            else:
                                db.update_cell('Tasks', int(data[3]), 'priority', int(data[-1]))
                                task = db.get_item('Tasks', int(data[3]))
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                        elif data[4] == 'start':
                            if data[-1] == 'start':
                                a = [InlineKeyboardButton('Убрать дату',)]
                                sessions[chat_id].task_date_start = 0.0
                                calendar1, step = DetailedTelegramCalendar(calendar_id=1,
                                                                           min_date=datetime.date.today(),
                                                                           locale='ru').build()
                                                                           # additional_buttons=[{'text': 'Победа',
                                                                           #                     "callback_data": 'weqweq'}]).build()
                                text = 'Выберите дату'
                                keyb = calendar1
                                sessions[chat_id].last_cb = call.data
                            else:
                                # time output
                                if sessions[chat_id].task_date_start:
                                    sessions[chat_id].set_start_time(int(data[-1]))
                                db.update_cell('Tasks', int(data[3]), 'start', sessions[chat_id].task_date_start.timestamp())
                                task = db.get_item('Tasks', int(data[3]))
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                        elif data[4] == 'end':
                            if data[-1] == 'end':
                                sessions[chat_id].task_date_start = 0.0
                                calendar2, step = DetailedTelegramCalendar(calendar_id=2,
                                                                           min_date=datetime.date.today(),
                                                                           locale='ru').build()
                                text = 'Выберите дату'
                                keyb = calendar2
                                sessions[chat_id].last_cb = call.data
                            else:
                                # time output
                                sessions[chat_id].set_end_time(int(data[-1]))
                                db.update_cell('Tasks', int(data[3]), 'end',
                                               sessions[chat_id].task_date_end.timestamp())
                                task = db.get_item('Tasks', int(data[3]))
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                        elif data[4] == 'cat':
                            if data[-1] == 'cat':
                                text = f'Выберите категорию'
                                keyb = cat_keyb(call.data)
                            else:
                                db.update_cell('Tasks', int(data[3]), 'category_id', int(data[-1]))
                                task = db.get_item('Tasks', int(data[3]))  #
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                        elif data[4] == 'not_start':
                            if data[-1] == 'not_start':
                                text = f'Когда вам напомнить о начале задачи?'
                                keyb = reminder_keyb(call.data)
                            else:
                                if data[-1] == 'n':
                                    db.update_cell('Tasks', int(data[3]), 'notify_before_start', 0)
                                else:
                                    db.update_cell('Tasks', int(data[3]), 'notify_before_start', int(data[-1]))
                                task = db.get_item('Tasks', int(data[3]))  #
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                                if task[8]:
                                    proj = db.get_item('Projects', task[8])[0]
                                    if task[6] != proj[2]:
                                        keyb = change_task_keyb(';'.join(data[:4]))

                        elif data[4] == 'not_end':
                            if data[-1] == 'not_end':
                                text = f'Когда вам напомнить о начале задачи?'
                                keyb = reminder_keyb(call.data)
                            else:
                                if data[-1] == 'n':
                                    db.update_cell('Tasks', int(data[3]), 'notify_before_end', 0)
                                else:
                                    db.update_cell('Tasks', int(data[3]), 'notify_before_end', int(data[-1]))
                                task = db.get_item('Tasks', int(data[3]))  #
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                                if task[8]:
                                    proj = db.get_item('Projects', task[8])[0]
                                    if task[6] != proj[2]:
                                        keyb = change_task_keyb(';'.join(data[:4]))
                        elif data[4] == 'rep':
                            if data[-1] == 'rep':
                                text = f'Выберите интервал повтора уведомлений'
                                keyb = repeat_keyb(call.data)
                            else:
                                if data[-1] == 'n':
                                    db.update_cell('Tasks', int(data[3]), 'notify_every', 0)
                                else:
                                    db.update_cell('Tasks', int(data[3]), 'notify_every', int(data[-1]))
                                task = db.get_item('Tasks', int(data[3]))  #
                                if task:
                                    task = task[0]
                                    text = gen_task_text(task)
                                text += f'\n\nВыберите что вы хотите изменить в задаче'
                                keyb = change_task_keyb(';'.join(data[:4]), is_owned=True)
                                if task[8]:
                                    proj = db.get_item('Projects', task[8])[0]
                                    if task[6] != proj[2]:
                                        keyb = change_task_keyb(';'.join(data[:4]))

                        bot.edit_message_text(text,
                                              chat_id,
                                              message_id,
                                              reply_markup=keyb)
                    else:
                        call_start(call)
                        return

        elif data[1] == 'export':
            file_name = export(chat_id)
            with open(file_name, 'r', encoding='utf_8') as file:
                bot.send_document(chat_id, file)
            os.remove(file_name)

    # projects
    elif data[0] == 'p':
        if len(data) == 1:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=sessions[chat_id].bot_message.id,
                                  text='Выберите что вы хотите сделать или просмотреть',
                                  reply_markup=proj_keyb)
        elif len(data) == 2 or data[-1] == 'n' or data[2] == 'show' or data[-2] == 'm':
            if data[-2] == 'm':
                page = int(data[-1])
            else:
                page = 0
            if data[1] == 'a' and len(data) == 2 or data[1] == 'a' and len(data) == 4 and data[2] == 'm':
                projects = [(proj[1], proj[0]) for proj in db.get_projects_list(chat_id, owned=False)]
                if projects:
                    text = 'Выберите интересующий вас проект'
                    keyb = slider('p;a', projects, page, itemprefix='p;a;show', menu_callback_data='u;menu')
                else:
                    keyb = slider('do-nothing', [], menu_callback_data='u;menu')
                    text = 'Вы не участвуете ни в одном проекте'
            elif data[1] == 'o' and len(data) == 2 or data[1] == 'o' and len(data) == 4 and data[2]=='m':
                projects = [(proj[1], proj[0]) for proj in db.get_projects_list(chat_id)]
                if projects:
                    text = 'Выберите интересующий вас проект'
                    keyb = slider('p;o;', projects, page, itemprefix='p;o;show', menu_callback_data='u;menu')
                else:
                    keyb = slider('do-nothing', [], menu_callback_data='u;menu')
                    text = 'У вас нет своих проектов'
            elif data[1] == 'new':
                text = 'Введите имя проекта'
                keyb = None
                bot.register_next_step_handler(call.message, project_name_input)
            elif data[2] == 'show':
                if data[-1] == 'tasks' or data[-2] == 'tasks' and data[-1] == 'm':
                    if data[1] == 'a':
                        tasks = db.get_project_tasks(int(data[3]), chat_id)
                        if tasks:
                            text = f'Ваши задачи в рамках проекта {db.get_item("Projects", int(data[-2]))[0][1]}'  # to-do слайдер с задачами

                        else:
                            text = f'У вас нет задач в рамках проекта {db.get_item("Projects", int(data[-2]))[0][1]}'
                        tasks = [
                            (f'{complition_to_emoji[task[7]]}' + task[1] + f'{priority_to_emoji[task[5]]}', task[0]) for task in tasks]
                        keyb = slider(f'p;a;show;{data[3]};tasks', tasks, page, itemprefix=f'p;a;show;{data[3]};task',
                                      menu_callback_data='u;menu')
                    elif data[1] == 'o':
                        tasks = db.get_project_tasks(int(data[3]))
                        if tasks:
                            text = f'Задачи проекта {db.get_item("Projects", int(data[-2]))[0][1]}'  # to-do слайдер с задачами
                        else:
                            text = f'В проекте {db.get_item("Projects", int(data[-2]))[0][1]} пока что нет задач'
                        tasks = [(f'{complition_to_emoji[task[7]]}'+ db.get_item('Users', task[6])[0][2] + ': ' + task[1]+f'{priority_to_emoji[task[5]]}', task[0]) for task in tasks]
                        keyb = slider(f'p;o;show;{data[3]};tasks', tasks, page, itemprefix=f'p;o;show;{data[3]};task', menu_callback_data='u;menu')
                    sessions[chat_id].set_last_cb(call.data)
                elif len(data) == 4:
                    proj = db.get_item('Projects', data[-1])[0]
                    text = f'Проект: {proj[1]}\nСсылка для присоединения к проекту {bot_link}?start=join_{proj[0]} (пройти и нажать старт)'
                    sessions[chat_id].set_selected_project(proj[0])
                    keyb = show_proj_keyb(f'p;{data[1]};show;{proj[0]}', db.get_item('Users', chat_id, 'chat_id')[0][0] == proj[2])
                    sessions[chat_id].set_last_cb(call.data)

                elif data[-1] == 'del' or data[-2] == 'del':
                    if data[-1] == 'del':
                        name = db.get_item('Projects', int(data[3]))
                        if name:
                            name = name[0][1]
                        else:
                            call_start(call)
                            return
                        text = f'Вы уверены что хотите удалить проект {name}?\nВсе задачи принадлежащие этому проекту будут удалены\nЭто действие нельзя отменить'
                        keyb = keybool(f'p;o;show;{data[-2]};del')
                    elif data[-1] == 'y':
                        name = db.get_item('Projects', int(data[3]))
                        if name and sessions[chat_id].last_cb != 'u;menu':
                            name = name[0][1]
                            db.del_project(int(data[3]))
                            text = f'Проект "{name} успешно удалён"'
                            keyb = keyb = slider('do-nothing', [], menu_callback_data='u;menu')
                        else:
                            call_start(call)
                            return
                    elif data[-1] == 'n':
                        name = db.get_item('Projects', int(data[3]))
                        if name and sessions[chat_id].last_cb != 'u;menu':
                            name = name[0][1]
                            proj = db.get_item('Projects', data[3])[0]
                            text = str(proj) + f'\nссылка для присоединения к проекту {bot_link}?start=join_{proj[0]}'
                            sessions[chat_id].set_selected_project(proj[0])
                            keyb = show_proj_keyb(f'p;{data[1]};show;{proj[0]}',
                                                  db.get_item('Users', chat_id, 'chat_id')[0][0] == proj[2])
                        else:
                            call_start(call)
                            return
                else:
                    if data[1] == 'o':
                        keyb = show_keyb(sessions[chat_id].last_cb, int(data[-1]))
                    elif data[1] == 'a':
                        keyb = show_keyb(sessions[chat_id].last_cb, int(data[-1]))
                    text = gen_task_text(db.get_item('Tasks', int(data[-1]))[0])

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=sessions[chat_id].bot_message.id,
                                  text=text,
                                  reply_markup=keyb)
        # elif len(data) == 3:
        elif data[1] == 'connect':
            user_id = db.get_item('Users', chat_id, 'chat_id')[0][0]
            text = f'Чтобы привязать канал к проекту, пригласите этого бота ({bot.get_my_name().name}) в канал который вы создали, и ❗внутри канала❗ отправьте следующую команду: \n/connect_{data[-1]}_{user_id}'
            keyb = slider('do-nothing', [], menu_callback_data='u;menu')
            bot.edit_message_text(text, chat_id,sessions[chat_id].bot_message.id, reply_markup=keyb)
        elif data[1] == 'new':
            if len(data) == 2:
                bot.edit_message_text(message_id=sessions[chat_id].bot_message.id,
                                      text='Введите имя проекта')
            elif len(data) == 3:
                db.create_project(sessions[chat_id].project_name, chat_id)
                call_start(call)


print('ready')
bot.infinity_polling()
