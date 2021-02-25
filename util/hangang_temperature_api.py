from datetime import datetime
from json import loads
from urllib.request import urlopen

from typing import Tuple


def get_hangang_temperature() -> Tuple[dict, datetime, str]:
    information = loads(urlopen('https://api.qwer.pw/request/hangang_temp?apikey=guest').read())[1]
    respond = information['respond']

    measured_at = datetime(int(respond['year']), int(respond['month']), int(respond['day']), int(respond['time']))

    return information, measured_at, respond['location']
