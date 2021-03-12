from pymysql.cursors import DictCursor

from util import database


class EconomyManager:
    @staticmethod
    def get_account(member_id: int) -> dict:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM wallet WHERE id = %s;', member_id)
            if data := cursor.fetchall():
                return data[0]
            else:
                return dict()

    @staticmethod
    def get_length() -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM wallet;')
            return cursor.fetchall()[0][0]

    @staticmethod
    def get_leaderboard(length: int = 15) -> tuple:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM wallet ORDER BY property DESC LIMIT %s;', length)
            return cursor.fetchall()

    @staticmethod
    def new_account(member_id: int, *, force: bool = True) -> dict:
        if force or not EconomyManager.get_account(member_id):
            with database.cursor() as cursor:
                cursor.execute('INSERT INTO wallet VALUES(%s, 0.0);', member_id)
            database.commit()
        return EconomyManager.get_account(member_id)

    @staticmethod
    def give(member_id: int, amount: float):
        account = EconomyManager.get_account(member_id)
        with database.cursor() as cursor:
            cursor.execute('UPDATE wallet SET property = %s WHERE id = %s;', (account['property'] + amount, member_id))
        database.commit()
