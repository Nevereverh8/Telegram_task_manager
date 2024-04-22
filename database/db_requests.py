import datetime
import sqlite3
database = sqlite3.connect('database/db.sqlite', check_same_thread=False)


class DataBase:
    def __init__(self):
        global database
        self.db = database

    def get_item(self, table: str, value: any, by='id'):
        """
        Returns record from table by any given field (by id as default)

        :rtype: tuple
        """
        if type(value) == str:
            value = "'" + value + "'"
        with self.db as con:
            return con.execute(f'''SELECT * FROM {table}
                            WHERE {by} = {value}''').fetchall()

    def update_cell(self, table: str, id: int, param: str, value: any):
        """
        Sets parameter(param) of item(by id) in table(table) to (value)
        """
        if type(value) == str:
            value = "'"+value+"'"
        with self.db as con:
            con.execute(f'''UPDATE {table}
                            SET '{param}' = {value}
                            WHERE id = {id} ''')

    def del_item(self, table: str, value: any, by='id'):
        """
        Deletes record(s) from table by any given field (by id as default)
        """
        if type(value) == str:
            value = "'"+value+"'"
        with self.db as con:
            con.execute(f'''DELETE FROM {table}
                            WHERE {by} = {value}''')

    def get_categories(self):
        with self.db as con:
            return(con.execute('SELECT * FROM Categories').fetchall())

    def create_user(self, chat_id, first_name='', last_name=''):
        with self.db as con:
             insert = '''
                        INSERT INTO Users (chat_id, first_name, last_name) VALUES (?,?,?)
                        '''
             con.execute(insert, [chat_id, first_name, last_name])

    def create_task(self, chat_id, name, cat_id, start, end, priority, notify_before_start=0, notify_before_end=0, notify_every=0, project_id=0):
        with self.db as con:
            if type(end) == datetime.datetime:
                end = end.timestamp()
            if type(start) == datetime.datetime:
                start = start.timestamp()
            user_id = db.get_item('Users', chat_id, by='chat_id')[0][0]
            insert = '''
                        INSERT INTO Tasks (name, category_id, start, end, priority, project_id, user_id, is_finished, notify_before_start, notify_before_end, notify_every) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        '''
            con.execute(insert, [name, cat_id, start, end, priority, project_id, user_id, 0, notify_before_start, notify_before_end, notify_every])
            return con.execute(f'''SELECT max(id) FROM Tasks WHERE user_id = {user_id}''').fetchone()

    def get_users_tasks(self, chat_id: int, date1=datetime.datetime(1970, 1, 1), date2: datetime.datetime = datetime.datetime(5000, 1, 1), condition='all'):
        with self.db as con:
            # all user tasks
            if condition == 'all':
                return con.execute(f'''SELECT * FROM Tasks WHERE user_id = (SELECT id FROM Users WHERE chat_id  = ?) AND is_finished = 0 ORDER BY start, end''', [chat_id]).fetchall()
            # tasks that start/end on a single date
            date1 = date1.timestamp()
            if condition in ['start', 'end']:
                date1 += 10800
                date1 = date1 - date1 % 86400 - 10800
                if date2 == datetime.datetime(5000, 1, 1):
                    date2 = date1 + 86399
                else:
                    date2 = date2.timestamp()
                    date2 += 10800
                    date2 = date2 - date2 % 86400 - 10800
                # print(f'''SELECT * FROM Tasks WHERE user_id = (SELECT id FROM Users WHERE chat_id  = ?) AND is_finished = 0 AND {condition} BETWEEN {date1} AND {date2}''')
                return con.execute(
                    f'''SELECT * FROM Tasks WHERE user_id = (SELECT id FROM Users WHERE chat_id  = ?) AND is_finished = 0 AND {condition} BETWEEN {date1} AND {date2} ORDER BY start, end''',
                    [chat_id]).fetchall()
            # now active task
            elif condition == 'actv':
                now = datetime.datetime.now()
                print(date1 == datetime.datetime(now.year, now.month, now.day).timestamp())
                if date1 == datetime.datetime(now.year, now.month, now.day).timestamp():
                    date1 += now.hour*3600 + now.minute*60 + now.second
                return con.execute(
                    f'''SELECT * FROM Tasks WHERE user_id = (SELECT id FROM Users WHERE chat_id  = ?) AND is_finished = 0 AND ({date1} >= start AND ({date1} < end OR end = 0.0)) ORDER BY start, end''',
                    [chat_id]).fetchall()

    def export(self, chat_id: int):
        with self.db as con:

            tasks = con.execute(f'''SELECT Tasks.name, Categories.name, Projects.name, priority, start, end  FROM Tasks
                                    LEFT JOIN Projects ON Projects.id = Tasks.project_id 
                                    INNER JOIN Categories ON Categories.id = Tasks.category_id
                                    WHERE user_id = (SELECT id FROM Users WHERE chat_id  = ?) AND is_finished = 0 ORDER BY start, end''', [chat_id]).fetchall()
            tasks = [('Название', 'Категория', 'Проект', 'Приоритет', 'Начало', 'Конец')] + tasks
        return tasks


    def get_tasks_with_remind(self):
        with self.db as con:
            # print(datetime.datetime.now().timestamp())
            tasks = con.execute(f'''SELECT Tasks.id, chat_id, name, start, start - notify_before_start * 60, end, end - notify_before_end * 60, notify_every FROM Tasks
                                    INNER JOIN Users ON Tasks.user_id = Users.id
                                    WHERE (start - notify_before_start * 60 - {datetime.datetime.now().timestamp()} BETWEEN 0 AND 300
                                    AND notify_before_start != 0)
                                    OR (end - notify_before_end * 60 - {datetime.datetime.now().timestamp()} BETWEEN 0 AND 300
                                    AND notify_before_end != 0)
                                    ''').fetchall()
        return tasks

    def get_projects_list(self, chat_id, owned=True):
        with self.db as con:
            if owned:
                return con.execute(f'''SELECT id, name FROM Projects
                                       WHERE creator_id = (SELECT id FROM Users WHERE chat_id  = {chat_id})
                                       ''').fetchall()
            else:
                return con.execute(f'''SELECT id, name FROM Projects
                                       WHERE id IN (SELECT project_id FROM Users_lists
                                                    WHERE user_id == (SELECT id FROM Users WHERE chat_id  = {chat_id})
                                                    )
                                       ''').fetchall()

    def get_project_tasks(self, project_id, chat_id=0):
        with self.db as con:
            if chat_id:
                return con.execute(f'''SELECT * FROM Tasks
                                       WHERE project_id == {project_id} and user_id = (SELECT id FROM Users WHERE chat_id = {chat_id})
                                       ''').fetchall()
            else:
                return con.execute(f'''SELECT * FROM Tasks
                                       WHERE project_id == {project_id}
                                       ''').fetchall()

    def create_project(self, name, chat_id):
        insert_proj = '''INSERT INTO Projects (name, creator_id) VALUES (?, ?)'''
        inser_user_list = '''INSERT INTO Users_lists (user_id, project_id) VALUES (?, ?)'''
        with self.db as con:
            creator_id = self.get_item('Users', chat_id, 'chat_id')[0][0]
            con.execute(insert_proj, [name, creator_id])

            project_id = con.execute(f'SELECT max(id) FROM Projects WHERE creator_id = {creator_id}').fetchone()[0]
            con.execute(inser_user_list, [creator_id, project_id])

    def get_project_users(self, project_id):
        with self.db as con:
            print(con.execute(f'''SELECT * FROM Users
                            WHERE id IN (SELECT user_id FROM Users_lists
                                        WHERE project_id == {project_id})''').fetchall())
            return con.execute(f'''SELECT * FROM Users
                            WHERE id IN (SELECT user_id FROM Users_lists
                                        WHERE project_id == {project_id})''').fetchall()

    def join_project(self, project_id, chat_id):
        with self.db as con:
            user_id = self.get_item('Users', chat_id, 'chat_id')[0][0]
            if not con.execute(f'''SELECT * FROM Users_lists WHERE user_id = {user_id} AND project_id = {project_id}''').fetchone() \
                    and self.get_item('Projects', project_id):
                insert = (f'''INSERT INTO Users_lists (user_id, project_id) VALUES (?, ?)''')
                con.execute(insert, [user_id, project_id])

    def del_project(self, proj_id):
        with self.db as con:
            con.execute(f'''DELETE FROM Tasks WHERE project_id = {proj_id}''')
            con.execute(f'''DELETE FROM Users_lists WHERE project_id = {proj_id}''')
            con.execute(F'''DELETE FROM Projects WHERE id = {proj_id}''')

sessions = {}
reminders = {}
reminders_to_del = []

db = DataBase()

if __name__ == '__main__':
    with database as con:
        # Tasks
        con.execute('''
                       CREATE TABLE IF NOT EXISTS Tasks(
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       name TEXT,
                       category_id INTEGER,    
                       start REAL,
                       end REAL,
                       priority INTEGER,
                       user_id INTEGER,
                       is_finished INTEGER,
                       project_id INTEGER,
                       notify_before_start INTEGER,
                       notify_before_end INTEGER,
                       notify_every INTEGER) 
                       ''')
        # Users
        con.execute('''
                       CREATE TABLE IF NOT EXISTS Users(
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       chat_id INTEGER,
                       first_name TEXT, 
                       last_name TEXT) 
                       ''')
        # Projects
        con.execute('''
                       CREATE TABLE IF NOT EXISTS Projects(
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       name TEXT,
                       creator_id INTEGER,
                       channel_id INTEGER) 
                       ''')
        # Categories
        con.execute('''
                       CREATE TABLE IF NOT EXISTS Categories(
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       name TEXT) 
                       ''')

        # Fill Categories
        insert_cat = '''
                        INSERT INTO Categories (name) VALUES (?)
                        '''
        categories = [["работа"], ["дом"], ["здоровье"], ["отдых"], ['другое']]
        con.executemany(insert_cat, categories)

        # Users_lists
        con.execute('''
                       CREATE TABLE IF NOT EXISTS Users_lists(
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       user_id TEXT,
                       project_id INTEGER) 
                       ''')

