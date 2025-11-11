import sys

from PyQt6 import QtCore
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from usermanager import UserManagementSystem
from widgets import GreetWidget, UserCreation, MainWidget, PasswordCreation, PasswordAuth


class MainWindow(QMainWindow):
    '''Класс основного окна

    -----------------------------------------------------------------------------------------------------------------

    Атрибуты:

    usermanager: class
        Экземпляр менеджера учетных данных

    -----------------------------------------------------------------------------------------------------------------

    Методы:

    create_greet_widget()
        Создает виджет входа и добавляет его в widget_stack

    create_main_widget()
        Создает главный виджет и добавляет его в widget_stack

    update_user_list()
        Обновляет меню combobox, добавляя в него новых пользователей

    get_entered_passw()
        Возвращает введенный пароль при входе

    open_user_creation_window()
        Открывает меню регистрации пользователя

    auth_with_pin()
        Пытается войти в пользователя с PIN-кодом

    log_out()
        Выходит из пользователя

    auth_with_password()
        Вход с паролем

    TODO:: реализовать блокировку входа по ПИН-коду после нескольких неудачных попыток
        (удалить мастер-ключ от ПИН-кода безвозвратно, после входа заставить придумать новый PIN и записать в БД)

    '''

    def __init__(self):
        super().__init__()

        QFontDatabase.addApplicationFont('fonts/Bahnschrift.ttf')
        QFontDatabase.applicationFontFamilies(0)

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(470, 900)
        self.setWindowTitle('myKey')

        self.usermanager = UserManagementSystem()

        self.isLoggedState = False
        self.user_session = None
        self.widget_stack = QStackedWidget()
        self.setCentralWidget(self.widget_stack)
        self.create_main_widget()
        self.create_greet_widget()
        self.widget_stack.setCurrentIndex(1)

    def create_greet_widget(self):  # создать виджет входа
        self.greet_widget = GreetWidget(self)
        self.widget_stack.addWidget(self.greet_widget)
        self.update_user_list()

    def isLogged(self):
        return self.isLoggedState

    def get_user_session(self):
        return self.user_session

    def set_current_session(self, username, master_key):
        self.user_session = (username, master_key)
        self.isLoggedState = True

    def update_user_list(self):  # обновить список
        self.greet_widget.user_comboBox.clear()
        for user in self.usermanager.get_users_list():
            self.greet_widget.user_comboBox.addItem(user[0])

    def create_main_widget(self):  # создать главный виджет
        self.main_widget = MainWidget(self, self.usermanager)
        self.widget_stack.addWidget(self.main_widget)

    def get_entered_passw(self):  # вернуть пароль
        return self.greet_widget.return_entered_passw()

    def open_user_creation_window(self):  # открыть меню создания пользователя
        if not self.isLogged():
            creation_window = UserCreation(self, usermanager=self.usermanager)
            creation_window.exec()
            self.update_user_list()

    def open_password_creation_window(self):
        if self.isLogged():
            creation_window = PasswordCreation(self, self.usermanager, self.main_widget)
            creation_window.exec()
            self.main_widget.show_info_message('Data successfully added')
            self.main_widget.show_data()

    def mousePressEvent(self, ev):
        self.dragPos = ev.globalPosition().toPoint()

    def mouseMoveEvent(self, ev):
        try:
            self.move(self.pos() + ev.globalPosition().toPoint() - self.dragPos)
            self.dragPos = ev.globalPosition().toPoint()
        except AttributeError:
            pass
        finally:
            ev.accept()

    def auth_with_pin(self):  # войти по пин-коду
        if not self.isLogged():
            current_user = self.greet_widget.user_comboBox.currentText()
            pin = self.get_entered_passw()
            if (current_user,) in self.usermanager.get_users_list():
                result = self.usermanager.get_master_key_with_pin(current_user, pin)
                if result[0]:
                    self.set_current_session(current_user, result[1])
                    self.main_widget.username_label.setText(current_user)
                    self.main_widget.create_user_session(self.get_user_session())
                    self.widget_stack.setCurrentIndex(0)
                else:
                    self.greet_widget.label.setText(result[1])
                    self.greet_widget.clear_input()

    def auth_with_password(self):  # войти по паролю (DEL)
        if not self.isLogged():
            current_user = self.greet_widget.user_comboBox.currentText()
            passw_auth = PasswordAuth(self, self.usermanager, current_user, 'Enter your password to log in')
            passw_auth.exec()
            if (current_user,) in self.usermanager.get_users_list() and self.isLogged() and self.get_user_session():

                self.main_widget.username_label.setText(current_user)
                self.main_widget.create_user_session(self.get_user_session())
                self.widget_stack.setCurrentIndex(0)

            else:
                self.greet_widget.label.setText('Password authentication failed.')
                self.greet_widget.clear_input()
                self.isLoggedState = False
                self.user_session = None

    def log_out(self):  # выйти
        if self.isLogged():
            self.widget_stack.setCurrentIndex(1)
            self.greet_widget.clear_input()
            self.greet_widget.label.setText('Enter your PIN-code')
            self.isLoggedState = False
            self.user_session = None

    def delete_user(self): # удаление пользователя (CTRL+DEL)
        if not self.isLogged():
            current_user = self.greet_widget.user_comboBox.currentText()
            passw_auth = PasswordAuth(self, self.usermanager, current_user, f"Confirm deletion of User: {current_user}")
            passw_auth.exec()
            if (current_user,) in self.usermanager.get_users_list() and self.isLogged() and self.get_user_session():
                result = self.usermanager.delete_user(current_user)
                if result[0]:
                    self.greet_widget.label.setText(result[1])
                    self.greet_widget.clear_input()
                    self.update_user_list()
            else:
                self.greet_widget.label.setText('Password authentication failed.')
                self.greet_widget.clear_input()
        self.isLoggedState = False
        self.user_session = None


def except_hook(cls, exception, traceback):
    sys.excepthook(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.excepthook = except_hook
    ex.show()
    sys.exit(app.exec())
