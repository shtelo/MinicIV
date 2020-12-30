from json import load

__strings = dict()
__const = dict()


def load_strings():
    global __strings

    with open('./res/strings.json', 'r', encoding='utf-8') as file:
        __strings = load(file)


def get_strings():
    return __strings


def load_const():
    global __const

    with open('./res/const.json', 'r') as file:
        __const = load(file)


def get_const():
    return __const


load_strings()
load_const()
