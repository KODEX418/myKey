import json
import sqlite3

from crypto import CryptographySystem
from config import DATABASE_NAME

class UserManagementSystem:
    """Класс менеджера учетных данных

        ---------------------------------------------------------------------------------------------------------------
        !!!ВАЖНО: ПРИ УДАЛЕНИИ ДАННЫХ ПОЛЬЗОВАТЕЛЯ ИЗ ТАБЛИЦЫ USERS ПАРОЛИ В USERDATA,
        СВЯЗАННЫЕ С НИМ, НЕ ПОДЛЕЖАТ ВОССТАНОВЛЕНИЮ!!!
        ---------------------------------------------------------------------------------------------------------------

        Атрибуты:

        db_path: str
            Имя базы данных

        crypto: class
            Экземпляр системы шифрования

        ---------------------------------------------------------------------------------------------------------------
        Методы:

        init_database()
            Создает (если не существует) базу данных с данными пользователей

        register_user(username, password, pin)
            Создает учетную запись пользователя и записывает в БД

        get_master_key_with_pin(username, pin)
            Возвращает результат расшифровки мастер-ключа

        get_master_key_with_password(username, passw)
            Возвращает результат расшифровки мастер-ключа

        get_users_list()
            Возвращает список пользователей

        write_user_data(username, master_key, data)
            Записывает словарь data в БД под пользователем username

        read_user_data(username, master_key)
            Возвращает данные пользователя username из БД

        delete_user_data(u_id)
            Удаляет данные пользователя с внутренним id = u_id

        delete_user(username)
            Удаляет пользователя и все данные, связанные с ним

        """

    def __init__(self, db_path=DATABASE_NAME):
        self.db_path = db_path
        self.crypto = CryptographySystem()
        self.init_database()

    def init_database(self):
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            command1 = '''CREATE TABLE IF NOT EXISTS users (
        id                    INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT,
        username              TEXT    UNIQUE
                                      NOT NULL
                                      ON CONFLICT ROLLBACK,
        image                 BLOB            ,
        master_key_passw      BLOB    NOT NULL,
        master_key_passw_salt BLOB    NOT NULL,
        master_key_pin        BLOB    NOT NULL,
        master_key_pin_salt   BLOB    NOT NULL
    );'''
            cur.execute(command1)  # создаем бд пользователей
            command2 = '''CREATE TABLE IF NOT EXISTS data (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL
                               REFERENCES users (id),
        encrypted_data BLOB    NOT NULL
    );
    '''
            cur.execute(command2)  # создаем бд учетных данных
            con.commit()
            con.close()
        except Exception:
            pass

    def register_user(self, username, password, pin, image=None):  # регистрируем пользователя
        userdata = self.crypto.derive_userdata(password=password, pin=pin)
        # passw_key, passw_key_salt, pin_key, pin_key_salt = userdata
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            if image:
                cur.execute(
                    '''INSERT INTO users 
                    (username, image, master_key_passw, master_key_passw_salt, master_key_pin, master_key_pin_salt) 
                    VALUES (?,?,?,?,?,?)''',
                    (username, image, *userdata))
            else:
                cur.execute(
                    '''INSERT INTO users 
                    (username, master_key_passw, master_key_passw_salt, master_key_pin, master_key_pin_salt) 
                    VALUES (?,?,?,?,?)''',
                    (username, *userdata))
            con.commit()
            con.close()
        except sqlite3.IntegrityError as e:
            if str(e) == 'UNIQUE constraint failed: users.username':
                return False, f'Username {username} is already registered'
            else:
                return False, f'SQL Error: {str(e)}'
        else:
            return True, f'User {username} successfully registered'

    def get_master_key_with_pin(self, username, pin=None):  # расшифровать мастер-ключ
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        if pin:
            cur.execute('''SELECT master_key_pin, master_key_pin_salt FROM users WHERE username = ?''', (username,))
            userdata = cur.fetchone()
            key = self.crypto.derive_key(pin, userdata[1])
        else:
            return False, 'Enter correct PIN'
        try:
            master_key = self.crypto.decrypt_data(userdata[0], key)
            return True, master_key
        except ValueError:
            return False, 'Incorrect PIN, try again'

    def get_master_key_with_password(self, username, passw=None):  # расшифровать мастер-ключ
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        if passw:
            cur.execute('''SELECT master_key_passw, master_key_passw_salt FROM users WHERE username = ?''', (username,))
            userdata = cur.fetchone()
            key = self.crypto.derive_key(passw, userdata[1])
        else:
            return False, 'Enter correct password'
        try:
            master_key = self.crypto.decrypt_data(userdata[0], key)
            return True, master_key
        except ValueError:
            return False, 'Incorrect password, try again'

    def get_users_list(self):  # вернуть список пользователей
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('''SELECT username, image FROM users''')
        users = cur.fetchall()
        return users

    def write_user_data(self, username, master_key, data):  # запись пользовательских данных
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        encr_data = [(self.crypto.encrypt_data(json.dumps(datum).encode(), master_key),) for datum in data]
        try:
            cur.executemany(
                F'''INSERT INTO data (user_id, encrypted_data) VALUES((SELECT id FROM users WHERE username = '{username}'),?)''',
                encr_data)
            con.commit()
            con.close()
        except Exception:
            return False, 'SQL error, try again'
        else:
            return True, 'Data successfully added'

    def read_user_data(self, username, master_key):  # чтение пользовательских данных
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        try:
            cur.execute(
                '''SELECT id, encrypted_data FROM data WHERE user_id = (SELECT id FROM users WHERE username = ?)''',
                (username,))
            encr_data = cur.fetchall()
        except Exception as e:
            return False, str(e)
        else:
            data = []
            try:
                for encr_datum in encr_data:
                    decrypted_datum = self.crypto.decrypt_data(encr_datum[1], master_key)
                    data.append([encr_datum[0], json.loads(decrypted_datum.decode('utf8'))])
            except Exception as e:
                return False, str(e)
            else:
                return True, data

    def delete_user_data(self, ud_id):  # удаление пользовательских данных
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        try:
            cur.execute('''DELETE from data where id = ?''', (ud_id,))
            con.commit()
            con.close()
        except Exception as e:
            return False, str(e)
        else:
            return True, 'Data successfully deleted'

    def delete_user(self, username):  # удаление пользователя и его данных
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        try:
            cur.execute('''DELETE FROM data WHERE user_id = (SELECT id FROM users Where username = ?)''', (username,))
            cur.execute('''DELETE FROM users where username = ?''', (username,))
            con.commit()
            con.close()
        except Exception as e:
            return False, str(e)
        else:
            return True, f'User {username} successfully deleted'

um = UserManagementSystem()
# # # # print(um.register_user('kodex', 'c1ff2g3', '4108'))
# # # print(um.register_user('user1', '88112233', '412143'))
# # # print(*um.get_users_list())
# userdata1 = {'descr':'yandex', 'login':'kdx', 'password':'aszaAAd!?'}
# userdata2 = {'descr':'mail', 'login':'holy_cow@index.com', 'password':'Milk228#'}
# #
# mkey = um.get_master_key_with_pin('tu1', '111111')[1]
# print(um.write_user_data('tu1', mkey, userdata1))
# print(um.write_user_data('tu1', mkey, userdata2))
# print(um.read_user_data('tu1', mkey))
print(um.delete_user('tu1'))