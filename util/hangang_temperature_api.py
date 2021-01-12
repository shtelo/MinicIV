from json import loads
from urllib.request import urlopen


def get_hangang_temperature() -> dict:
    return loads(urlopen('http://hangang.dkserver.wo.tc/').read())
