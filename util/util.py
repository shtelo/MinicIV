from os import environ

from pymysql import connect


def strawberrify(hangul: str) -> tuple:
    hangul = ord(hangul) - 44032
    jong = ' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'[hangul % 28]
    jung = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'[hangul // 28 % 21]
    cho = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'[hangul // 28 // 21 % 19]
    return cho, jung, jong


def get_keys(sentence: str) -> int:
    keys = 0
    for letter in sentence:
        if 44032 <= ord(letter) <= 55203:  # 44032: 가, 55203: 힣
            cho, jung, jong = strawberrify(letter)
            if cho in 'ㄲㄸㅃㅆㅉ':
                keys += 2
            else:
                keys += 1
            if jung in 'ㅒㅖㅘㅙㅚㅝㅞㅟ':
                keys += 2
            else:
                keys += 1
            if jong in 'ㄲㄳㄵㄶㄺㄻㄼㄽㄾㄿㅀㅄ':
                keys += 2
            elif jong == ' ':
                pass
            else:
                keys += 1
        elif letter in '~!@#$%^&*()_+|':
            keys += 2
        else:
            keys += 1
    return keys


database = connect(
    user=environ['MINIC_DATABASE_USER'],
    passwd=environ['MINIC_DATABASE_PASSWD'],
    host='sch.shtelo.org',
    db='shtelo',
    charset='utf8'
)
