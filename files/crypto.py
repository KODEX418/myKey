import json
import os
import secrets
import string

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptographySystem:
    """Класс шифрования данных

    ------------------------------------------------------------------------------------------------------------------

    Принцип работы:

    Создание пользовательских данных
                        (Пароль + Cоль1) / (PIN + Соль2) → derive_key → Ключ1 / Ключ2
                                    ↓               ↓                         ↓
                                    ↓               ↓                  encrypt_data ← Мастер-ключ (32 рандомных бита)
                                    →   РЕЗУЛЬТАТ   ←                         ↓
                                            ↑----------------   ЗашифрМ-ключ1 / ЗашифрМ-ключ2

    ------------------------------------------------------------------------------------------------------------------

    Методы:

    get_master_key()
        Возвращает рандомные 32 бита данных (ИСПРАВЛЕНО В СООТВЕТСТВИИ С СТАНДАРТАМИ КРИПТОГРАФИИ)

    derive_key(passw, salt):
        Возвращает ключ шифрования(HASH-значение пароля password с солью salt)

    encrypt_data(data, key):
        Шифрует введенные данные data с помощью ключа key

    encrypt_data(encr_data, key):
         Дешифрует введенные данные encr_data с помощью ключа key

    derive_userdata(password, pin):
        Выпускает готовые к записи в БД зашифрованные данные

    """

    def __init__(self):
        self.backend = default_backend()

    def get_master_key(self):  # мастер-ключ
        return secrets.token_bytes(32)
        # return os.urandom(32)

    def derive_key(self, passw: str, salt: bytes):  # выпустить ключ шифрования из пароля/PIN и cоли
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=10 ** 5,
            backend=self.backend
        )
        return kdf.derive(passw.encode())  # вернуть ключ шифрования

    def encrypt_data(self, data, key):  # зашифровать данные (и мастер ключ и сами данные)
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithm=algorithms.AES256(key), backend=self.backend, mode=modes.CBC(iv))
        encryptor = cipher.encryptor()
        pad = padding.PKCS7(128).padder()
        padded_data = pad.update(data) + pad.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return iv + encrypted_data  # вернуть зашифрованные данные

    def decrypt_data(self, encr_data, key):  # расшифровать данные (и мастер ключ и сами данные)
        iv = encr_data[:16]
        data = encr_data[16:]
        cipher = Cipher(algorithm=algorithms.AES256(key), backend=self.backend, mode=modes.CBC(iv))
        decryptor = cipher.decryptor()
        encrypted_data = decryptor.update(data) + decryptor.finalize()
        unpad = padding.PKCS7(128).unpadder()
        final_data = unpad.update(encrypted_data) + unpad.finalize()
        return final_data  # вернуть данные

    def derive_userdata(self, password, pin):  # выпустить пользовательские данные из пароля и PIN
        master_key = self.get_master_key()  # мастер-ключ
        passw_salt = secrets.token_bytes(16)  # соль пароля
        pin_salt = secrets.token_bytes(16)  # соль PIN-кода
        password_key = self.derive_key(passw=password, salt=passw_salt)  # ключ из пароля и его соли
        pin_key = self.derive_key(passw=pin, salt=pin_salt)  # ключ из PIN-кода и его соли
        master_key_password = self.encrypt_data(master_key, password_key)  # зашифрованный ключом мастер-ключ
        master_key_pin = self.encrypt_data(master_key, pin_key)  # зашифрованный ключом мастер-ключ
        return master_key_password, passw_salt, master_key_pin, pin_salt  # возвращает готовые к записи в бд данные


def generate_password(length, use_upper=True, use_lower=True, use_digits=True, use_symb=True): # безопасная генерация пароля
    spec_symb = '!#@$%_'
    characters = string.ascii_uppercase * use_upper + string.ascii_lowercase * use_lower + string.digits * use_digits
    characters += spec_symb * use_symb
    if not any([use_upper, use_lower, use_digits, use_symb]):
        return None
    while True:
        passw = [secrets.choice(characters) for _ in range(length)]
        if (any(c.islower() for c in passw) or (not use_lower)) and (
                any(c.isupper() for c in passw) or (not use_upper)) and (
                (any(c.isdigit() for c in passw) or (not use_digits)) and (
                any(c in spec_symb for c in passw) or (not use_symb))):
            return ''.join(passw)


def example1():  # пример для отладки
    crypto = CryptographySystem()  # экземпляр криптосистемы

    mkey = crypto.get_master_key()  # мастер-ключ

    my_data = input('Ввведите данные: ')

    encrypted_data = crypto.encrypt_data(json.dumps(my_data).encode(), mkey)  # зашифрованные данные
    # init_passw = 'Qwerty123'
    init_passw = input('Введите пароль для шифрования: ')
    pass_salt = os.urandom(16)  # соль пароля
    passw_key = crypto.derive_key(init_passw, pass_salt)  # # ключ из пароля и соли
    encrypted_master_key = crypto.encrypt_data(mkey, passw_key)  # зашифрованный ключом из пароля мастер ключ
    print('Данные успешно зашифрованы\n')
    while True:
        entered_passw = input('Введите пароль для расшифровки: ')
        # entered_passw = 'Qwerty123'# введенный пароль
        ent_p_key = crypto.derive_key(entered_passw, pass_salt)  # сгененированный ключ из пароля
        try:
            decrypted_master_key = crypto.decrypt_data(encrypted_master_key,
                                                       ent_p_key)  # выдаст ошибку ValueError при неправильном пароле
            decrypted_data = crypto.decrypt_data(encrypted_data, decrypted_master_key)  # выдает json-данные
        except ValueError:
            print('Неверный пароль ')
        else:
            break
    print('Успешно')
    print(json.loads(decrypted_data.decode('utf8')))  # выводит готовые данные

# while True:
#     input()
#     print(generate_password(8, use_symb=False))
