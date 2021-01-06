from datetime import datetime
from difflib import ndiff
from random import choice
from typing import Optional
from unicodedata import east_asian_width

from discord import TextChannel, Message
from pymysql.cursors import DictCursor

from util import database, get_keys


class TypingGame:
    """진행중인 타자연습 게임에 대한 정보를 저장하는 객체의 클래스입니다."""

    def __init__(self, channel: TextChannel, sentence: tuple):
        """
        :param channel: 타자연습이 진행중인 TextChannel
        :param sentence: 진행중인 타자연습 문장. (문자열, 문장 ID)
        :var self.started: 타자연습을 시작한 시각
        :var self.message: 미닉이 보낸, 타자연습 문장을 담은 Message
        :var self.keys: 문장을 입력하는 데에 필요한 타수
        """
        self.channel = channel
        self.sentence = sentence[0]
        self.sentence_id = sentence[1]
        self.started: Optional[datetime] = None
        self.message: Optional[Message] = None
        self.keys = get_keys(self.sentence)

    def start(self):
        self.started = datetime.now()
        return self

    def set_message(self, message: Message):
        self.message = message
        return self

    def calculate(self, time: datetime) -> tuple:
        """
        self.started 부터 time 까지동안 이 문장을 입력해 완료되었다면 얼마나 빨리 문장을 입력했는지 계산하여 출력합니다.
        :return: (입력시간, 타수[타/분])
        """
        delta = (time - self.started)
        delta = delta.seconds + delta.microseconds / 1_000_000
        return delta, self.keys / delta * 60


class TypingManager:
    """타자연습 문장을 슈텔로 데이터베이스에 등록하고 가져오는 등의 작업을 수행합니다."""

    KOREAN = 0
    ENGLISH = 1
    JAPANESE = 2

    LANGUAGE_CODE = {'한국어': KOREAN, '영어': ENGLISH, '일본어': JAPANESE}
    LANGUAGE_CODE_REVERSED = {v: k for k, v in LANGUAGE_CODE.items()}

    def __init__(self):
        self.games = dict()

    @staticmethod
    def get_diff(before: str, after: str) -> str:
        result = list(ndiff([before], [after]))
        for i in range(len(result)):
            result[i] = list(result[i])
            if result[i][0] == '?':
                for j in range(2, len(result[i])):
                    print(result[i][j], end='')
                    if east_asian_width(result[i-1][j]) in 'FW':
                        if result[i][j] == '+':
                            result[i][j] = '＋'
                        elif result[i][j] == '-':
                            result[i][j] = '－'
                        elif result[i][j] == ' ':
                            result[i][j] = '　'
                        elif result[i][j] == '^':
                            result[i][j] = '＾'
            result[i] = ''.join(result[i])
        return '\n'.join(result)

    @staticmethod
    def get_sentences(language: int = 0) -> tuple:
        """언어가 language 인 모든 문장을 dict 형태로 가져옵니다."""
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM typing_sentence WHERE language = %s;', language)
            return cursor.fetchall()

    @staticmethod
    def get_sentence(language: int = 0) -> tuple:
        """언어가 language 인 랜덤 문장을 dict 형태로 가져옵니다."""
        return choice(TypingManager.get_sentences(language))

    @staticmethod
    def get_sentence_by_id(id_: int) -> dict:
        """id 가 id_인 문장을 dict 형태로 가져옵니다."""
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM typing_sentence WHERE id = %s', id_)
            if data := cursor.fetchall():
                return data[0]
            else:
                return dict()

    @staticmethod
    def get_leaders_length() -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM typing_record;')
            return cursor.fetchall()[0][0]

    @staticmethod
    def get_sentences_length() -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM typing_sentence;')
            return cursor.fetchall()[0][0]

    @staticmethod
    def acheatablify(sentence: str) -> str:
        """복붙을 통한 통과를 방지하기 위해 문장을 불가편법화(acheatablify)합니다."""
        return chr(8203).join(list(sentence))

    @staticmethod
    def get_recording(member_id: int, language: int) -> dict:
        """id 가 member_id 인 멤버가 language 언어로 낸 기록을 dict 형태로 가져옵니다."""
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM typing_record WHERE author = %s AND language = %s', (member_id, language))
        if data := cursor.fetchall():
            return data[0]
        else:
            return dict()

    @staticmethod
    def check_and_record(member_id: int, language: int, speed: float):
        """
        기록을 데이터베이스에 작성합니다.
        :param language: 기록할 언어 코드
        :param member_id: 기록할 타자(打者)
        :param speed: 타자 속도 [타/분]
        """
        with database.cursor() as cursor:
            if recording := TypingManager.get_recording(member_id, language):
                if speed > recording['record']:
                    cursor.execute('UPDATE typing_record SET record = %s WHERE author = %s AND language = %s;',
                                   (speed, member_id, language))
            else:
                cursor.execute('INSERT INTO typing_record VALUES(%s, %s, %s)', (member_id, language, speed))
        database.commit()

    @staticmethod
    def get_records_ordered(limit: int = 20, language: int = -1) -> tuple:
        """언어가 language 인 dict 형태의 기록을 limit 개 불러옵니다."""
        with database.cursor(DictCursor) as cursor:
            if language != -1:
                cursor.execute('SELECT * FROM typing_record WHERE language = %s ORDER BY record DESC LIMIT %s',
                               (language, limit))
            else:
                cursor.execute('SELECT * FROM typing_record ORDER BY record DESC LIMIT %s', limit)
            return cursor.fetchall()

    @staticmethod
    def update_sentence(sentence_id: int, sentence: str):
        """id 가 sentence_id 인 문장을 sentence 로 갱신합니다."""
        with database.cursor() as cursor:
            cursor.execute('UPDATE typing_sentence SET content = %s WHERE id = %s', (sentence, sentence_id))
        database.commit()

    @staticmethod
    def delete_record(member_id: int):
        """
        타자가 member_id 인 기록을 모두 삭제합니다.
        이 기능은 타자가 서버에서 찾아지지 않을 때에 사용합니다.
        """
        with database.cursor() as cursor:
            cursor.execute('DELETE FROM typing_record WHERE author = %s', member_id)
        database.commit()

    @staticmethod
    def get_sentence_by_content(sentence: str):
        """내용이 sentence 인 문장을 dict 형태로 1개 불러옵니다."""
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM typing_sentence WHERE content = %s', sentence)
        if data := cursor.fetchall():
            return data[0]
        else:
            dict()

    @staticmethod
    def add_sentence(language: int, content: str) -> int:
        """
        데이터베이스에 문장을 등록합니다.
        :param language: 문장의 언어 (코드)
        :param content: 문장 내용
        :return: 등록된 문장의 DB 상 ID
        """
        with database.cursor(DictCursor) as cursor:
            cursor.execute('INSERT INTO typing_sentence(content, language) VALUES(%s, %s);', (content, language))
        database.commit()
        return TypingManager.get_sentence_by_content(content)['id']

    def add_game(self, typing_game: TypingGame):
        """
        진행중인 게임 목록에 typing_game 을 추가합니다.
        이는 cog 에서 게임 관리자로 작동할 때 사용됩니다.
        """
        self.games[typing_game.channel.id] = typing_game.start()
