from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_requests import db
# PM keyboards

'''
Legend
y - yes
n - no

u - user
    t - tasks
        new - new task
            1-5 - step number
            s - task start related
            e - task end related

        today - show tasks for today
        cal - chose date to show tasks
    p - projects
a - project administrator    


'''


# main menu keyboard
main_menu_keyb = InlineKeyboardMarkup()
main_menu_keyb.add(InlineKeyboardButton('Задачи', callback_data='u;t'))
main_menu_keyb.add(InlineKeyboardButton('Проекты', callback_data='p'))


# task menu keyboard
task_keyb = InlineKeyboardMarkup()
task_keyb.add(InlineKeyboardButton('Задачи на сегодня', callback_data='u;t;date;now'))
task_keyb.add(InlineKeyboardButton('Задачи на дату', callback_data='u;t;date;cal'))
task_keyb.add(InlineKeyboardButton('Задачи на 7 дней', callback_data='u;t;date;week'))
task_keyb.add(InlineKeyboardButton('Создать новую задачу', callback_data='u;t;new;0r'))
task_keyb.add(InlineKeyboardButton('Скачать задачи', callback_data='u;export'))
task_keyb.add(InlineKeyboardButton('Меню', callback_data='u;menu'))

no_task_keyb = InlineKeyboardMarkup()
no_task_keyb.add(InlineKeyboardButton('Создать новую задачу', callback_data='u;t;new;0r'))
no_task_keyb.add(InlineKeyboardButton('Меню', callback_data='u;menu'))

# task name input keyboard
name_keyb = InlineKeyboardMarkup()
name_keyb.add(InlineKeyboardButton('В меню', callback_data='u;menu'),
              InlineKeyboardButton('Изменить', callback_data='u;t;new;0r'),
              InlineKeyboardButton('Далее', callback_data='u;t;new;1'))

def step_keyb(menu_data, reset_data, next_step_data):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('В главаное меню', callback_data=menu_data),
             InlineKeyboardButton('Изменить', callback_data=reset_data),
             InlineKeyboardButton('Далее', callback_data=next_step_data))
    return keyb


# task cat keyboard
def cat_keyb(prefix):
    keyb = InlineKeyboardMarkup()
    cats = db.get_categories()
    for i in range(len(cats)//2+len(cats)%2):
        if 2 * i + 1 < len(cats):
            keyb.add(InlineKeyboardButton(cats[2 * i][1], callback_data=f'{prefix};'+str(cats[2 * i][0])),
                         InlineKeyboardButton(cats[2 * i + 1][1], callback_data=f'{prefix};'+str(cats[2 * i+1][0])))
        else:
            keyb.add(InlineKeyboardButton(cats[2 * i][1], callback_data=f'{prefix};'+str(cats[2 * i][0])))
    keyb.add(InlineKeyboardButton('Отмена', callback_data='u;menu'),
                 InlineKeyboardButton('Назад', callback_data='u;t;new;0'))
    return keyb


# priority choice keyboard
def priority_keyb(prefix):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('Высокий 🔴', callback_data=f'{prefix};3'))
    keyb.add(InlineKeyboardButton('Средний 🟡', callback_data=f'{prefix};2'))
    keyb.add(InlineKeyboardButton('Низкий 🟢', callback_data=f'{prefix};1'))
    return keyb



# reminder keyboard
def reminder_keyb(prefix):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('за 10 минут', callback_data=f'{prefix};10'), InlineKeyboardButton('за 30 минут', callback_data=f'{prefix};30'))
    keyb.add(InlineKeyboardButton('за час до', callback_data=f'{prefix};60'), InlineKeyboardButton('за 2 часа', callback_data=f'{prefix};120'))
    keyb.add(InlineKeyboardButton('за 24 часа', callback_data=f'{prefix};1440'), InlineKeyboardButton('за неделю', callback_data=f'{prefix};10080'))
    keyb.add(InlineKeyboardButton('не напоминать', callback_data=f'{prefix};n'))
    return keyb


# universal yes/no keyboard
def keybool(prefix:str):
    """
    Default data separator is ';' easy to replace

    :param prefix: part of callback data before y/n, without last separator
    :return: InlineKeyboardMarkup two buttons in the same line
    """
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('Да', callback_data=prefix+';y'),
             InlineKeyboardButton('Нет', callback_data=prefix+';n'))
    return keyb


# universal time choice keyboard
def time_keyb(prefix, min_time=0):
    keyb = InlineKeyboardMarkup()
    time_list = [time for time in range(0, 24)]
    keyb.row_width = 4
    btn_list = [InlineKeyboardButton(f'{t}:00', callback_data=f'{prefix};{t}') for t in range(0, 24)]
    for i in range(3 - len(btn_list) % 4):
        btn_list.append(InlineKeyboardButton(f' ', callback_data='text_btn'))
    for i in range(len(btn_list) // 4):
        keyb.add(*btn_list[i * 4:i * 4 + 4])
    return keyb


# repeat interval choice keyboard
def repeat_keyb(prefix):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('раз в 5 мин.', callback_data=prefix+';5'),
             InlineKeyboardButton('раз в 10 мин.', callback_data=prefix+';10'),
             InlineKeyboardButton('раз в 15 мин.', callback_data=prefix+';15'))
    keyb.add(InlineKeyboardButton('раз в 30 мин.', callback_data=prefix+';30'),
             InlineKeyboardButton('раз в час', callback_data=prefix+';60'),
             InlineKeyboardButton('раз в 3 часа', callback_data=prefix+';180'))
    keyb.add(InlineKeyboardButton('раз в день', callback_data=prefix+';1440'),
             InlineKeyboardButton('раз в неделю', callback_data=prefix+';10080'))
    keyb.add(InlineKeyboardButton('не повторять', callback_data=prefix+';n'))
    return keyb


# task types keyb
def task_types_keyb(prefix):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('Запланированные', callback_data=prefix+';start'))
    keyb.add(InlineKeyboardButton('Завершающиеся', callback_data=prefix+';end'))
    if 'week' not in prefix:
        keyb.add(InlineKeyboardButton('Текущие', callback_data=prefix+';actv'))
    keyb.add(InlineKeyboardButton('Меню', callback_data='u;menu'))
    return keyb


# task list slider
def slider(prefix, listy, page=0, row_num=5, itemprefix='', menu_callback_data = 'menu'):
    '''

    :param prefix: part of callback data before item callback, without last separator
    :param listy: list of tuples [(btn_txt, btn_data), ...] (use list(dict.items()) to convert dict to list of tuples
    :param page: page number
    :param row_num: number of rows
    :param itemprefix: prefix for item btn_data(default=prefix param)
    :param menu_callback_data: callback for menu button
    :return: keyboard
    '''
    keyb = InlineKeyboardMarkup()

    if not itemprefix:
        itemprefix = prefix

    if listy:
        # reduce amount of rows by 1 if last page contains only one item (looks ugly)
        if len(listy) % row_num == 1 and len(listy) % (row_num - 1) != 1:  # check if it helps
            row_num -= 1
        # last page item index
        if ((page + 1) * row_num) < len(listy):
            end = ((page + 1) * row_num)
        else:
            end = len(listy)
        # page gen
        for i in range(page*row_num, end):
            keyb.add(InlineKeyboardButton(listy[i][0], callback_data=f'{itemprefix};{listy[i][1]}'))
        if page == 0 and end != len(listy):
            keyb.add(InlineKeyboardButton("Вперед", callback_data=f'{prefix};m;{str(page + 1)}'))   # m - for move to page
        elif page != 0 and end == len(listy):
            keyb.add(InlineKeyboardButton("Назад", callback_data=f'{prefix};m;{str(page - 1)}'))
        elif page != 0:
            keyb.add(InlineKeyboardButton("Назад", callback_data=f'{prefix};m;{str(page - 1)}'),
                     InlineKeyboardButton("Вперед", callback_data=f'{prefix};m;{str(page + 1)}'))
    if prefix == 'u;t;new;5':
        keyb.add(InlineKeyboardButton('Создать задачу внутри проекта и уведомить ответственных', callback_data=prefix+';save'))
    keyb.add(InlineKeyboardButton("Меню", callback_data=menu_callback_data))
    return keyb


def show_keyb(last_cb, task_id):
    keyb = InlineKeyboardMarkup()
    if not db.get_item('Tasks', task_id)[0][7]:
        keyb.add(InlineKeyboardButton('Завершить задачу',  callback_data=f'u;t;fin;{task_id}'))
    keyb.add(InlineKeyboardButton('Назад', callback_data=last_cb),
             InlineKeyboardButton("Меню", callback_data='u;menu'),
             InlineKeyboardButton('Изменть задачу', callback_data=f'u;t;change;{task_id}'))
    return keyb


# keyboard inside notification
def notification_keyb(task_id, is_assignment=False):
    keyb = InlineKeyboardMarkup()
    if not is_assignment:
        keyb.add(InlineKeyboardButton('Завершить задачу', callback_data=f'u;t;fin;{task_id}'))
        keyb.add(InlineKeyboardButton('Выключить повтор', callback_data=f'u;t;n;r;off;{task_id}'))
    keyb.add(InlineKeyboardButton('Закрыть', callback_data=f'u;t;n;close'))
    return keyb


proj_keyb = InlineKeyboardMarkup()
proj_keyb.add(InlineKeyboardButton('Проекты в которых я участвую', callback_data='p;a'))
proj_keyb.add(InlineKeyboardButton('Мои проекты', callback_data='p;o'))
proj_keyb.add(InlineKeyboardButton('Создать проект', callback_data='p;new'))
proj_keyb.add(InlineKeyboardButton("Меню", callback_data='u;menu'))


def show_proj_keyb(prefix, is_owned):
    keyb = InlineKeyboardMarkup()
    #if db.get_project_tasks(int(prefix.split(';')[-1])):
    keyb.add(InlineKeyboardButton("Просмотреть задачи", callback_data=prefix+';tasks'))
    if is_owned:
        if not db.get_item('Projects', int(prefix.split(';')[-1]))[0][3]:
            keyb.add(InlineKeyboardButton('Привязать телеграм канал к проекту', callback_data=f"p;connect;{prefix.split(';')[-1]}"))
        keyb.add(InlineKeyboardButton('Добавить задачу', callback_data='u;t;new;0r'))
        keyb.add(InlineKeyboardButton('Удилить проект', callback_data=prefix+';del'))
    keyb.add(InlineKeyboardButton("Меню", callback_data='u;menu'))
    return keyb


def change_task_keyb(prefix, is_owned=False):
    keyb = InlineKeyboardMarkup()
    task = db.get_item('Tasks', int(prefix.split(';')[3]))
    if task:
        task = task[0]
        if is_owned:
            keyb.add(InlineKeyboardButton('Название', callback_data=f'{prefix};name'),
                     InlineKeyboardButton('Категорию', callback_data=f'{prefix};cat'),
                     InlineKeyboardButton('Приоритет', callback_data=f'{prefix};prior')
                     )

            keyb.add(InlineKeyboardButton('Дату и время начала', callback_data=f'{prefix};start'),
                     InlineKeyboardButton('Дату и время конца', callback_data=f'{prefix};end'))
        if task[3]:
            keyb.add(InlineKeyboardButton('Уведомление к началу задачи', callback_data=f'{prefix};not_start'))
        if task[4]:
            keyb.add(InlineKeyboardButton('Уведомление к концу задачи', callback_data=f'{prefix};not_end'))
        if task[9] or task[10]:
            keyb.add(InlineKeyboardButton('Повтор уведомлений', callback_data=f'{prefix};rep'))
    keyb.add(InlineKeyboardButton("Меню", callback_data='u;menu'))
    return keyb

