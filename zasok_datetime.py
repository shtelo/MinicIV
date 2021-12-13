from sys import argv
from datetime import datetime, timedelta


class ZasokDatetime:
    @staticmethod
    def get_from_datetime(date):
        delta = date - datetime(2017, 12, 25)
        convert = (delta.days + (delta.seconds + delta.microseconds/1000000) / 86400) / 7 * 20
        return ZasokDatetime(convert)

    def __init__(self, year: float, month: float = 1, day: float = 1, hour: float = 0, minute: float = 0, second: float = 0):
        minute += second / 60
        hour += minute / 60
        day += -1 + hour / 24
        month += -1 + day / 22
        year += month / 8

        self.year = 1
        self.month = 1
        self.day = 1
        self.hour = 0
        self.minute = 0
        self.second = 0.0

        self.refresh_by_year(year)

    def __str__(self):
        return f'{self.year}. {self.day:02d}. {self.month}. {self.hour:02d}:{self.minute:02d}:{self.second:02.6f}'

    def __repr__(self):
        return f'ZasokDatetime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second})'

    def refresh_by_year(self, year):
        year, month = int(year), (year - int(year)) * 8
        month, day = int(month) + 1, (month - int(month)) * 22
        day, hour = int(day) + 1, (day - int(day)) * 24
        hour, minute = int(hour), (hour - int(hour)) * 60
        minute, second = int(minute), (minute - int(minute)) * 60
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
    
    def get_on_year(self):
        minute = self.minute + self.second / 60
        hour = self.hour + minute / 60
        day = self.day-1 + hour / 24
        month = self.month-1 + day / 22
        year = self.year + month / 8
        return year

    def to_datetime(self):
        c = self.get_on_year()
        days_plus = c / 20 * 7
        return datetime(2017, 12, 25) + timedelta(days=days_plus)


if __name__ == '__main__':
    if len(argv) < 4:
        date = datetime.now()
    else:
        date = datetime(int(argv[1]), int(argv[2]), int(argv[3]))

    print(ZasokDatetime.get_from_datetime(date))

