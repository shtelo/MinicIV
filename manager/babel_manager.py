from pymysql.cursors import DictCursor

from util import database


class BabelManager:
    @staticmethod
    def get_leaderboard() -> tuple:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM babel WHERE floor > 1 ORDER BY floor DESC')
            return cursor.fetchall()

    @staticmethod
    def get_leader(member_id: int):
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM babel WHERE member_id = %s', member_id)
            if data := cursor.fetchall():
                return data[0]
            else:
                return dict()

    @staticmethod
    def up(member_id: int, delta: int):
        with database.cursor(DictCursor) as cursor:
            if leader := BabelManager.get_leader(member_id):
                floor = max(leader['floor'] + delta, 1)
                cursor.execute('UPDATE babel SET floor = %s WHERE member_id = %s', (floor, member_id))
            else:
                cursor.execute('INSERT INTO babel VALUES(%s, %s)', (member_id, max(delta, 1)))
