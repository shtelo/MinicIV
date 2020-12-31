from pymysql.cursors import DictCursor

from util import database


class Memo:
    def __init__(self, content: str, author_id: int):
        self.content: str = content
        self.author_id: int = author_id


class MemoManager:
    @staticmethod
    def get(key: str) -> Memo:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT * FROM memos WHERE `key` = %s;', key)
            result = cursor.fetchall()[0]
            return Memo(result['value'], result['author_id'])

    @staticmethod
    def get_value(key: str) -> str:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT value FROM memos WHERE `key` = %s;', key)
            data = cursor.fetchall()
            return data[0]['value']

    @staticmethod
    def get_keys() -> tuple:
        cursor = database.cursor()
        cursor.execute('SELECT `key` FROM memos;')
        return tuple([column[0] for column in cursor.fetchall()])

    @staticmethod
    def get_author_id(key: str) -> int:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT author_id FROM memos WHERE `key` = %s;', key)
            data = cursor.fetchall()
            return data[0]['author_id']

    @staticmethod
    def insert(key: str, memo: Memo):
        cursor = database.cursor()
        cursor.execute('INSERT INTO memos VALUES(%s, %s, %s);', (key, memo.content, memo.author_id))
        database.commit()

    @staticmethod
    def update(key: str, memo: Memo):
        cursor = database.cursor()
        cursor.execute('UPDATE memos SET value = %s WHERE `key` = %s;', (memo.content, key))
        database.commit()

    @staticmethod
    def delete(key: str):
        cursor = database.cursor()
        cursor.execute('DELETE FROM memos WHERE `key` = %s;', key)
        database.commit()

    @staticmethod
    def is_key(key: str) -> bool:
        cursor = database.cursor()
        return cursor.execute('SELECT * FROM memos WHERE `key` = %s;', key)