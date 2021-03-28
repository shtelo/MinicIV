from datetime import datetime

from flask_restful import Resource, Api

from manager import ShteloTime


class ShtelianCalendar(Resource):
    @staticmethod
    def get():
        shtelo_time = ShteloTime.by_datetime(datetime.now())
        return {
            'term': shtelo_time.term,
            'week': shtelo_time.week,
            'day_of_the_week': shtelo_time.day,
            'string': str(shtelo_time)
        }


def setup(api: Api):
    api.add_resource(ShtelianCalendar, '/shtelian_calendar')
