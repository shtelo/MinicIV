from datetime import datetime, timedelta
from json import loads
from urllib.request import urlopen

from typing import Tuple


def get_hangang_temperature() -> Tuple[dict, datetime, str]:
    information = loads(urlopen('https://api.qwer.pw/request/hangang_temp?apikey=guest').read())[1]
    respond = information['respond']

    if (time := int(respond['time'])) < 24:
        measured_at = datetime(int(respond['year']), int(respond['month']), int(respond['day']), time)
    else:
        measured_at = datetime(int(respond['year']), int(respond['month']), int(respond['day']), time - 24) \
                      + timedelta(days=1)

    return information, measured_at, respond['location']
