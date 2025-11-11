import string

from PyQt6 import QtCore
from PyQt6.QtGui import QKeyEvent, QCursor
from PyQt6.QtWidgets import QDialog, QLineEdit, QWidget, QHeaderView, QApplication, QToolTip

from crypto import generate_password
from design_files.greet_widget_design import Ui_Form as GreetWidgetUi
from design_files.main_widget_design import Ui_Form as MainWidgetUi
from design_files.password_auth_design import Ui_Dialog as PasswordAuthUi
from design_files.password_dialog_design import Ui_Dialog as PasswordCreationUi
from design_files.user_creation_design import Ui_Dialog as UserCreationUi
from table_model import TableModel
from usermanager import UserManagementSystem

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class GreetWidget(QWidget, GreetWidgetUi):
    '''
    Класс логики виджета входа.

    ------------------------------------------------------------------------------------------------------------------

    Дизайн - GreetWidgetUi

    ------------------------------------------------------------------------------------------------------------------

    Атрибуты:

    passw_lineEdit_text : str
        Введенный пользователем PIN-код (только цифры)

    ------------------------------------------------------------------------------------------------------------------

    Методы:

    add_digit(digit)
        Метод для ввода с виртуальной клавиатуры. Добавляет символ digit в passw_lineEdit

    del_digit()
        Метод для ввода с виртуальной клавиатуры. Удаляет последний символ в passw_lineEdit

    clear_input()
        Метод для ввода с виртуальной клавиатуры. Очищает passw_lineEdit. Также работает по нажатию кнопки DEL

    return_entered_passw()
        Возвращает введенный PIN-код.
    '''

    def __init__(self, window):
        super().__init__()

        # uic.loadUi('greet_widget_design.ui', self)
        self.setupUi(self)
        self.window = window
        self.passw_lineEdit_text = ''
        self.passw_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passw_lineEdit.setReadOnly(True)

        for btn in self.entry_buttonGroup.buttons():  # бинд кнопок entry
            if btn.text() == 'E':
                pass
            elif btn.text() == '<':
                btn.clicked.connect(self.del_digit)
            else:
                btn.clicked.connect(lambda x, y=btn.text(): self.add_digit(y))

        # self.setFocusPolicy(QtCore.Qt.FocusPolicy.TabFocus)
        self.quitButton.clicked.connect(self.window.close)
        self.add_userButton.clicked.connect(self.window.open_user_creation_window)
        self.pushButton_enter.clicked.connect(self.window.auth_with_pin)

    def add_digit(self, d):  # дописать символ в passw_lineEdit
        self.passw_lineEdit_text += d
        self.passw_lineEdit.setText(self.passw_lineEdit_text)

    def del_digit(self):  # удалить символ из passw_lineEdit
        self.passw_lineEdit_text = self.passw_lineEdit_text[:-1]
        self.passw_lineEdit.setText(self.passw_lineEdit_text)

    def clear_input(self):  # очистить ввод
        self.passw_lineEdit_text = ''
        self.passw_lineEdit.setText(self.passw_lineEdit_text)

    def keyPressEvent(self, event: QKeyEvent):  # обработка значений с клавиатуры
        if isinstance(event, QKeyEvent):
            if event.text().isdigit():
                self.add_digit(event.text())
            elif event.key() == QtCore.Qt.Key.Key_Backspace:
                self.del_digit()
            elif event.key() == QtCore.Qt.Key.Key_F8:
                if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                    self.window.delete_user()
                else:
                    self.window.auth_with_password()
            elif event.key() == QtCore.Qt.Key.Key_Delete:
                self.clear_input()

            elif event.key() == QtCore.Qt.Key.Key_Return:
                self.window.auth_with_pin()

    def return_entered_passw(self):  # вернуть введенный пароль
        return self.passw_lineEdit_text


class UserCreation(QDialog, UserCreationUi):
    '''
    Класс логики диалогового окна создания пользователя.

    ------------------------------------------------------------------------------------------------------------------

    Дизайн - UserCreationUi

    ------------------------------------------------------------------------------------------------------------------

    Атрибуты:

    window : class
        Родительское окно
    um : class
        Экземпляр менеджера учетных записей

    ------------------------------------------------------------------------------------------------------------------

    Методы:

    show_chars()
        Переключает режим показа пароля и PIN-кода на видимый

    hide_chars()
        Переключает режим показа пароля и PIN-кода на скрытый

    validate_username()
        Проверяет, что введено корректное имя пользователя

    validate_password()
        Проверяет, что введен корректный пароль

    validate_password()
        Проверяет, что введен корректный PIN-код

    try_create_user()
        Проверяет правильность введенных данных и создает пользователя

    show_error_message(message)
        Выводит строку message в error_label
    '''

    def __init__(self, window, usermanager=None):
        super().__init__()
        self.window = window
        self.um = usermanager
        # uic.loadUi('user_creation_design.ui', self)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.cancel_button.clicked.connect(self.reject)
        self.create_button.clicked.connect(self.try_create_user)

        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_char_button.pressed.connect(self.show_chars)
        self.show_char_button.released.connect(self.hide_chars)
        self.user_lineEdit.setPlaceholderText('len>1, only latin')
        self.password_lineEdit.setPlaceholderText('len>7, upper, lower, numbers, !#@$%_')
        self.pin_lineEdit.setPlaceholderText('len>5, only numbers')

    def show_chars(self):
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Normal)
        self.pin_lineEdit.setEchoMode(QLineEdit.EchoMode.Normal)

    def hide_chars(self):
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

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

    def validate_login(self):  # валидация username
        keys = []
        login = self.user_lineEdit.text()
        is_login_long_enough = len(login) > 1
        login_cont_only_latin = all(k in string.ascii_letters or k in string.digits or k in '!#@$%_' for k in login)

        keys.append(is_login_long_enough)
        keys.append(login_cont_only_latin)

        return all(keys)  # возвращает выполнение всех ключей

    def validate_password(self):  # валидация пароля
        passw = list(self.password_lineEdit.text())
        keys = []

        is_passw_long_enough = len(passw) >= 8
        passw_cont_numbers = any(k in passw for k in string.digits)
        passw_cont_special_symbols = any(k in passw for k in '!#@$%_')
        passw_cont_low_symbols = any(k in passw for k in string.ascii_lowercase)
        passw_cont_up_symbols = any(k in passw for k in string.ascii_uppercase)
        passw_cont_only_latin = all(k in string.ascii_letters or k in string.digits or k in '!#@$%_' for k in passw)

        keys.append(is_passw_long_enough)
        keys.append(passw_cont_numbers)
        keys.append(passw_cont_special_symbols)
        keys.append(passw_cont_low_symbols)
        keys.append(passw_cont_up_symbols)
        keys.append(passw_cont_only_latin)

        return all(keys)  # возвращает выполнение всех ключей

    def validate_pin(self):  # валидация pin
        pin = self.pin_lineEdit.text()
        keys = []

        is_pin_long_enough = len(pin) >= 6
        pin_cont_only_numbers = all(k.isdigit() for k in list(pin))

        keys.append(is_pin_long_enough)
        keys.append(pin_cont_only_numbers)

        return all(keys)  # возвращает выполнение всех ключей

    def try_create_user(self):  # проверка условий
        if not self.validate_login():
            self.show_error_message('Incorrect login')
        elif not self.validate_password():
            self.show_error_message('Incorrect password')
        elif not self.validate_pin():
            self.show_error_message('Incorrect PIN')
        else:
            if self.um:
                username = self.user_lineEdit.text()
                password = self.password_lineEdit.text()
                pin = self.pin_lineEdit.text()
                result = self.um.register_user(username, password, pin)
                self.show_error_message(result[1])

    def show_error_message(self, message: str):  # вывести сообщение
        self.error_label.setText(message)


class PasswordAuth(QDialog, PasswordAuthUi):
    '''
        Класс логики диалогового окна входа через пароль. Используется для аутентификации

        ------------------------------------------------------------------------------------------------------------------

        Дизайн - GreetWidgetUi

        ------------------------------------------------------------------------------------------------------------------

        Атрибуты:

        window: class
            Родительское окно
        um: class
            Экземпляр менеджера учетных данных
        current_user: str
            Имя пользователя

        ------------------------------------------------------------------------------------------------------------------

        Методы:

        show_chars()
            Переключает режим показа пароля и PIN-кода на видимый

        hide_chars()
            Переключает режим показа пароля и PIN-кода на скрытый

        validate_password()
            Проверяет введенный пароль и передает мастер-ключ

        '''

    def __init__(self, window, um, current_user, text):
        super().__init__()
        self.window = window
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.cancel_button.clicked.connect(self.reject)
        self.accept_button.clicked.connect(self.validate_password)
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_char_button.pressed.connect(self.show_chars)
        self.show_char_button.released.connect(self.hide_chars)
        self.um = um
        self.current_user = current_user
        self.info_label.setText(text)

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

    def show_chars(self):  # показать пароль
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Normal)

    def hide_chars(self):  # скрыть пароль
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

    def show_error_message(self, message: str):  # вывести сообщение
        self.error_label.setText(message)

    def validate_password(self):  # проверить пароль
        password = self.password_lineEdit.text()
        if (self.current_user,) in self.um.get_users_list():
            result = self.um.get_master_key_with_password(self.current_user, password)
            if result[0]:
                self.window.set_current_session(self.current_user, result[1])
                self.reject()
            else:
                self.show_error_message(result[1])


class MainWidget(QWidget, MainWidgetUi):
    def __init__(self, window, usermanager: UserManagementSystem):
        super().__init__()
        self.setupUi(self)
        self.search_edit.setPlaceholderText('Search by name')

        self.window = window
        self.um = usermanager
        self.log_out_button.clicked.connect(self.window.log_out)
        self.quitButton.clicked.connect(self.window.close)
        self.add_data_button.clicked.connect(self.window.open_password_creation_window)
        self.delete_data_button.clicked.connect(self.del_data)
        self.tableView.doubleClicked.connect(self.on_double_click)

    def create_table_model(self):

        self.table_model = TableModel()
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.table_model)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)
        self.tableView.setModel(self.proxy)
        self.tableView.setSortingEnabled(True)
        self.search_edit.textChanged.connect(self.proxy.setFilterFixedString)
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

    def create_user_session(self, user_session):
        self.info_label.clear()
        self.user_session = user_session
        self.create_table_model()
        self.show_data()

    def on_double_click(self, index):
        source_index = self.proxy.mapToSource(index)

        real_password = self.table_model._rows[source_index.row()][source_index.column()]

        # Мгновенное копирование
        clipboard = QApplication.clipboard()
        clipboard.setText(real_password)

        # Краткое уведомление
        self.show_quick_notification("Copied to clipboard!")
        self.show_info_message("Copied to clipboard!")

    def show_quick_notification(self, msg):
        QToolTip.showText(
            QCursor.pos(),
            msg,
            self.tableView,
            QtCore.QRect(),
            msecShowTime=100000
        )

    def load_data(self):
        if not self.user_session:
            return None
        result = self.um.read_user_data(self.user_session[0], self.user_session[1])
        if result[0]:
            data = result[1]
            return data

    def show_data(self):
        data = self.load_data()
        if not data:
            return
        headers = ['Description', 'Username', 'Password']
        trans_data = [list(d[1].values()) for d in data] if data else []
        self.table_model.beginResetModel()
        self.internal_id = {j[1]['name'] + '-cocoa-' + j[1]['username']: j[0] for j in data}  # внутренний id
        self.table_model._headers = headers
        self.table_model._rows = trans_data
        self.table_model.endResetModel()

    def show_info_message(self, msg):
        self.info_label.setText(msg)

    def del_data(self):  # удалить один пароль
        ind = self.tableView.selectionModel().selectedIndexes()
        if len(ind) != 3:
            self.show_info_message('Select whole row to Delete')
            return
        key = '-cocoa-'.join([self.proxy.data(i, 0) for i in ind[:-1]])  # выбранные данные
        if key not in self.internal_id.keys():
            return
        result = self.um.delete_user_data(self.internal_id[key])
        if result[0]:
            self.show_data()
        self.show_info_message(result[1])


class PasswordCreation(QDialog, PasswordCreationUi):
    '''
        Класс логики диалогового окна добавления пароля.

        ------------------------------------------------------------------------------------------------------------------

        Дизайн - PasswordCreationUi

        ------------------------------------------------------------------------------------------------------------------

        Атрибуты:

        window : class
            Родительское окно
        um : class
            Экземпляр менеджера учетных записей
        user_session: tuple
            Учетные данные пользователя
        ------------------------------------------------------------------------------------------------------------------

        Методы:

        show_chars()
            Переключает режим показа пароля и PIN-кода на видимый

        hide_chars()
            Переключает режим показа пароля и PIN-кода на скрытый

        show_error_message(message)
            Выводит строку message в error_label

        add_password()
            Добавляет пользовательские данные
        generate_password()
            Генерирует пароль
        '''

    def __init__(self, window, um, mw):
        super().__init__()

        self.window = window
        self.um = um
        self.mw = mw
        self.user_session = self.window.get_user_session()

        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.cancel_button.clicked.connect(self.reject)

        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_char_button.pressed.connect(self.show_chars)
        self.show_char_button.released.connect(self.hide_chars)
        self.generate_button.clicked.connect(self.generate_password)
        self.create_button.clicked.connect(self.add_password)

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

    def show_chars(self):  # показать пароль
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Normal)

    def hide_chars(self):  # скрыть пароль
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

    def show_error_message(self, message: str):  #
        self.error_label.setText(message)

    def generate_password(self):  # сгенерировать пароль
        passw_len = int(self.length_spinBox.text())
        use_upper = self.upper_checkBox.isChecked()
        use_lower = self.lower_checkBox.isChecked()
        use_digits = self.digits_checkBox.isChecked()
        use_symb = self.symb_checkBox.isChecked()
        password = generate_password(passw_len, use_upper=use_upper, use_lower=use_lower, use_digits=use_digits,
                                     use_symb=use_symb)
        if password:
            self.password_lineEdit.setText(password)
            self.show_error_message('Password successfully generated.')
        else:
            self.show_error_message('Select at least one modifier')

    def add_password(self):  # добавить пользовательские данные
        data = {
            'name': self.descr_lineEdit.text(),
            'username': self.login_lineEdit.text(),
            'password': self.password_lineEdit.text()
        }
        result = self.um.write_user_data(self.user_session[0], self.user_session[1], data)
        if result[0]:
            self.accept()
            self.mw.show_info_message(result[1])
        else:
            self.show_error_message(result[1])
