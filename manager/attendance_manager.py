from datetime import timedelta, date

from pymysql.cursors import DictCursor

from util import database


class AttendanceManager:
    @staticmethod
    def get_attendance(member_id: int):
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM attendance WHERE member_id = %s', member_id)
            if attendance := cursor.fetchall():
                return attendance[0]
            else:
                return dict()

    @staticmethod
    def get_length() -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM attendance;')
            return cursor.fetchall()[0][0]

    @staticmethod
    def attend(member_id: int) -> int:
        """
        member_id 로 출석합니다.
        :return: strike
        """
        attendance = AttendanceManager.get_attendance(member_id)
        today = date.today()
        with database.cursor(DictCursor) as cursor:
            if not attendance:
                cursor.execute('INSERT INTO attendance VALUES(%s, %s, %s)', (member_id, 1, today))
                database.commit()
                return 1
            elif attendance['date'] == today:
                return attendance['strike']
            elif attendance['date'] == today - timedelta(days=1):
                cursor.execute('UPDATE attendance SET strike = %s, date = %s WHERE member_id = %s',
                               (attendance['strike'] + 1, today, member_id))
                database.commit()
                return attendance['strike'] + 1
            else:
                cursor.execute('UPDATE attendance SET strike = 1, date = %s WHERE member_id = %s', (today, member_id))
                database.commit()
                return 1

    @staticmethod
    def get_leaderboard() -> tuple:
        with database.cursor() as cursor:
            cursor.execute('SELECT * FROM attendance ORDER BY strike DESC')
            return cursor.fetchall()
