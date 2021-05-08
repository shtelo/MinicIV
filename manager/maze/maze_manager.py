from pymysql.cursors import DictCursor

from util import database


class MazeManager:
    @staticmethod
    def get_leaderboard():
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM maze ORDER BY count DESC')
            return cursor.fetchall()

    @staticmethod
    def add_score(member_id: int):
        with database.cursor() as cursor:
            cursor.execute('SELECT * FROM maze')
            data = cursor.fetchall()
            data = dict(data)
            if str(member_id) in data:
                cursor.execute('UPDATE maze SET count = %s WHERE member_id = %s', (data[str(member_id)] + 1, member_id))
                database.commit()
                return data[str(member_id)] + 1
            else:
                cursor.execute('INSERT INTO maze VALUES(%s, 1)', member_id)
                database.commit()
                return 1
