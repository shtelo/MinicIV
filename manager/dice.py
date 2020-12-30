import re
from random import randint

from discord.ext import commands
from discord.ext.commands import Context


class Dice(commands.Converter):
    """몇 개의 주사위를 몇 번 돌릴지, 주사위 정보를 저장하고 주사위를 굴려주는 클래스입니다."""
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D20 = 20
    D_PERCENT = 100

    def __init__(self):
        self.count = 0
        self.dice: int = 0

    def __str__(self):
        return f'{self.count if self.count > 1 else ""}D{self.dice}'

    def roll(self) -> int:
        """
        객체(self)의 주사위 정보에 따라 주사위를 굴리고 그 숫자를 반환합니다.
        :return: 굴린 주사위 눈의 합
        """
        number = 0
        for _ in range(self.count):
            number += randint(1, self.dice)
        return number

    def set_count(self, count: int):
        """
        주사위의 개수를 지정합니다.
        :param count: 주사위 개수
        """
        self.count = count
        return self

    def set_dice(self, dice: int):
        """
        어떤 종류의 주사위를 사용할 것인지 정합니다.
        주사위 종류는 Dice 의 Static 변수로 받습니다.
        :param dice: 주사위 종류
        """
        self.dice = dice
        return self

    async def convert(self, ctx: Context, argument: str):
        """Discord converter. 문자열로 된 주사위 정보를 Dice 객체로 변환합니다."""

        if re.compile(r'\d*[dD](4|6|8|10|12|20|%|100)').match(argument):
            count, dice = argument.lower().split('d')
            count, dice = int(count) if count else 1, int(dice) if dice != '%' else 100
            return Dice().set_dice(dice).set_count(count)
        else:
            return
