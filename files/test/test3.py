import string


def validate_login(s):
    keys = []
    login = s

    is_login_long_enough = len(login) > 1
    login_cont_only_latin = all(k in string.ascii_letters or k in string.digits or k in '!#@$%_' for k in login)

    keys.append(is_login_long_enough)
    keys.append(login_cont_only_latin)

    return all(keys)


def validate_password(s):
    passw = s
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

    return all(keys)


def validate_pin(s):
    keys = []
    pin = s

    is_pin_long_enough = len(pin) >= 6
    pin_cont_only_numbers = all(k.isdigit() for k in list(pin))

    keys.append(is_pin_long_enough)
    keys.append(pin_cont_only_numbers)

    return all(keys)
a = 0
if a:
    print(1)
else:
    print(2)