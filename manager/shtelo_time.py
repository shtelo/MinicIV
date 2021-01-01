from datetime import datetime, timedelta

from discord.ext.commands import Converter, Context

from util import get_shtelo_times


class ShteloTime:
    START_POINTS = get_shtelo_times()

    DAY_TO_STR_KR = '일월화수목금토'

    @staticmethod
    def by_datetime(time: datetime):
        if time < ShteloTime.START_POINTS[0]:
            return

        tmp = None
        for i in range(len(ShteloTime.START_POINTS)):
            start_point = ShteloTime.START_POINTS[i] - timedelta(days=(ShteloTime.START_POINTS[i].weekday() + 1) % 7)
            if start_point <= time:
                tmp = start_point
            else:
                break

        term = 0
        for start_point in ShteloTime.START_POINTS:
            if start_point <= time:
                term += 1
            else:
                break

        delta = (time - tmp).days

        week = delta // 7
        day = delta % 7

        return ShteloTime(term, week, day)

    def __init__(self, term: int, week: int, day: int):
        self.term = term
        self.week = week
        self.day = day

    def __str__(self):
        return f'슈텔력 {self.term}기 {self.week}주 {ShteloTime.DAY_TO_STR_KR[self.day]}요일'

    def convert(self) -> datetime:
        if self.term > len(ShteloTime.START_POINTS):
            return
        start_point = ShteloTime.START_POINTS[self.term - 1]
        start_point -= timedelta(days=start_point.weekday())

        return start_point + timedelta(weeks=self.week, days=self.day - 1)


class WeekDay(int, Converter):
    async def convert(self, ctx: Context, argument: str):
        if argument.endswith('요일'):
            argument = argument[:-2]

        return ShteloTime.DAY_TO_STR_KR.index(argument)
