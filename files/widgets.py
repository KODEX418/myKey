import string
from csv import DictReader

from PIL import Image
from PyQt6 import QtCore
from PyQt6.QtGui import QKeyEvent, QCursor, QPixmap
from PyQt6.QtWidgets import QDialog, QLineEdit, QWidget, QApplication, QToolTip, QFileDialog
from PyQt6.QtCore import QBuffer, QByteArray
from config import CSV_IMPORT_HEADER, TABLE_HEADERS
from crypto import generate_password
from design_files.greet_widget_design import Ui_Form as GreetWidgetUi
from design_files.main_widget_design import Ui_Form as MainWidgetUi
from design_files.password_auth_design import Ui_Dialog as PasswordAuthUi
from design_files.password_dialog_design import Ui_Dialog as PasswordCreationUi
from design_files.user_creation_design import Ui_Dialog as UserCreationUi
from table_model import TableModel


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

    set_picture()
        Обновляет картинку
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
        self.user_comboBox.currentTextChanged.connect(self.set_picture)
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
            elif event.key() == QtCore.Qt.Key.Key_Delete:
                if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                    self.window.delete_user()
                else:
                    self.clear_input()
            elif event.key() == QtCore.Qt.Key.Key_F8:
                self.window.auth_with_password()
            elif event.key() == QtCore.Qt.Key.Key_Return:
                self.window.auth_with_pin()

    def return_entered_passw(self):  # вернуть введенный пароль
        return self.passw_lineEdit_text

    def set_picture(self):
        username = self.user_comboBox.currentText()
        if username in self.window.users_avatars.keys():
            if self.window.users_avatars[username]:
                self.user_picture.setPixmap(self.window.users_avatars[username])
                self.user_picture.update()
            else:
                self.user_picture.clear()
                self.user_picture.setText(username[0])
        else:
            if username:
                self.user_picture.setText(username[0])


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

    blob_image: bytes
        Изображение, выбранное пользователем в виде байтов

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

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.um = window.usermanager
        # uic.loadUi('user_creation_design.ui', self)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.cancel_button.clicked.connect(self.reject)
        self.create_button.clicked.connect(self.try_create_user)
        self.blob_image = None
        self.password_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_char_button.pressed.connect(self.show_chars)
        self.show_char_button.released.connect(self.hide_chars)
        self.user_lineEdit.setPlaceholderText('len>1, only latin')
        self.password_lineEdit.setPlaceholderText('len>7, upper, lower, numbers, !#@$%_')
        self.pin_lineEdit.setPlaceholderText('len>5, only numbers')
        self.color_pick_button.clicked.connect(self.get_image)

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
                image = self.blob_image if self.blob_image else None
                result = self.um.register_user(username, password, pin, image)
                self.show_error_message(result[1])

    def show_error_message(self, message: str):  # вывести сообщение
        self.error_label.setText(message)

    def get_image(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]
        if not fname:
            self.show_error_message('Select valid image')
            return
        else:
            self.show_error_message('Image successfully loaded')
        pixmap = QPixmap(fname).scaled(64, 64, QtCore.Qt.AspectRatioMode.IgnoreAspectRatio)
        self.blob_image = self.pixmap_to_bytes(pixmap)

    def pixmap_to_bytes(self, pixmap):
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")  # Сохраняем как PNG
        return byte_array.data()

class PasswordAuth(QDialog, PasswordAuthUi):
    '''
        Класс логики диалогового окна входа через пароль. Используется для аутентификации

        ------------------------------------------------------------------------------------------------------------------

        Дизайн - PasswordAuthUi

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

    def __init__(self, window, current_user, text):
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
        self.um = window.usermanager
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
        if self.current_user in [k[0] for k in self.um.get_users_list()]:
            result = self.um.get_master_key_with_password(self.current_user, password)
            if result[0]:
                self.window.set_current_session(self.current_user, result[1])
                self.reject()
            else:
                self.show_error_message(result[1])


class MainWidget(QWidget, MainWidgetUi):
    '''
            Класс логики основного окна входа.
            ------------------------------------------------------------------------------------------------------------------

            Дизайн - MainWidgetUi

            ------------------------------------------------------------------------------------------------------------------

            Атрибуты:

            window: class
                Родительское окно

            um: class
                Экземпляр менеджера учетных данных

            user_session: tuple
                Пользовательская сессия с учетными данными

            ------------------------------------------------------------------------------------------------------------------

            Методы:

            create_table_model()
                Создает модель таблицы

            create_user_session(user_session)
                Создает пользовательскую сессию и инициализирует таблицу

            copy_to_clipboard(index)
                Копирует выделенную ячейку таблицы в буфер обмена по двойному нажатию

            show_quick_notification(msg)
                Выводит tooltip с сообщением msg

            load_data()
                Возвращает данные из таблицы

            show_data()
                Отображает данные в таблице

            show_info_message()
                Показывает сообщение пользователю

            del_data()
                Удаляет выбранные данные из БД

            import_csv_data()
                Импортирует данные из CSV-файла

            '''

    def __init__(self, window):
        super().__init__()
        self.setupUi(self)
        self.search_edit.setPlaceholderText('Search by name')

        self.window = window
        self.um = window.usermanager
        self.log_out_button.clicked.connect(self.window.log_out)
        self.quitButton.clicked.connect(self.window.close)
        self.add_data_button.clicked.connect(self.window.open_password_creation_window)
        self.delete_data_button.clicked.connect(self.del_data)
        self.import_data_button.clicked.connect(self.import_csv_data)
        self.tableView.doubleClicked.connect(self.copy_to_clipboard)

    def create_table_model(self):  # создать модель таблицы

        self.table_model = TableModel()
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.table_model)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)
        self.tableView.setModel(self.proxy)
        self.tableView.setSortingEnabled(True)
        self.search_edit.textChanged.connect(self.proxy.setFilterFixedString)
        header = self.tableView.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(135)

    def create_user_session(self, user_session):  # создать пользовательскую сессию
        self.info_label.clear()
        self.user_session = user_session
        self.show_data()

    def copy_to_clipboard(self, index):  # скопировать в буфер обмена по двойному клику по ячейке
        source_index = self.proxy.mapToSource(index)

        real_password = self.table_model._rows[source_index.row()][source_index.column()]

        clipboard = QApplication.clipboard()
        clipboard.setText(real_password)

        self.show_quick_notification("Copied to clipboard!")
        self.show_info_message("Copied to clipboard!")

    def show_quick_notification(self, msg):  # отображение подсказки
        QToolTip.showText(
            QCursor.pos(),
            msg,
            self.tableView,
            QtCore.QRect(),
            msecShowTime=100000
        )

    def load_data(self):  # загрузить данные из бд
        if not self.user_session:
            return None
        result = self.um.read_user_data(self.user_session[0], self.user_session[1])
        if result[0]:
            data = result[1]
            return data

    def show_data(self):  # показать данные
        self.create_table_model()
        data = self.load_data()
        if not data:
            return

        trans_data = [list(d[1].values()) for d in data] if data else []

        self.internal_id = {j[1]['name'] + '~' + j[1]['username']: j[0] for j in data}  # внутренний id
        self.table_model._headers = TABLE_HEADERS
        self.table_model._rows = trans_data
        self.table_model.endResetModel()

    def show_info_message(self, msg):  # вывести сообщение
        self.info_label.setText(msg)

    def del_data(self):  # удалить один пароль
        ind = self.tableView.selectionModel().selectedIndexes()
        if len(ind) != 3:
            self.show_info_message('Select whole row to Delete')
            return
        key = '~'.join([self.proxy.data(i, 0) for i in ind[:-1]])  # выбранные данные
        if key not in self.internal_id.keys():
            self.show_info_message('Select whole row to Delete')
            return
        result = self.um.delete_user_data(self.internal_id[key])
        if result[0]:
            self.show_data()
        self.show_info_message(result[1])

    def import_csv_data(self):  # импорт данных из csv-таблицы
        filename = QFileDialog.getOpenFileName(self, 'Open CSV file', '', 'CSV files (*.csv)')[0]
        overall, added = 0, 0
        if not filename:
            return
        udata = []
        with open(filename, 'r', encoding='utf-8-sig') as file:
            rd = DictReader(file)
            for line in rd:
                try:
                    overall += 1

                    udatum = {
                        'name': line[CSV_IMPORT_HEADER[0]],
                        'username': line[CSV_IMPORT_HEADER[1]],
                        'password': line[CSV_IMPORT_HEADER[2]]
                    }
                    udata.append(udatum)
                    added += 1
                except KeyError:
                    continue
        result = self.um.write_user_data(self.user_session[0], self.user_session[1], reversed(udata))
        if result[0]:
            self.show_info_message(f'{added}/{overall} imported')
            self.show_data()
        else:
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

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.um = window.usermanager
        self.mw = window.main_widget
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

    def show_error_message(self, message: str):  # вывести сообщение
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

        result = self.um.write_user_data(self.user_session[0], self.user_session[1], [data])
        if result[0]:
            self.accept()
            self.mw.show_info_message(result[1])
        else:
            self.show_error_message(result[1])
