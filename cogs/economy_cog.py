import re
from asyncio import TimeoutError as AsyncioTimeoutError
from random import randint

from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context
from pymysql.cursors import DictCursor

from util import get_strings, database


def strings():
    return get_strings()['cog']['economy']


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


class UpdownGame:
    """Updown 게임 객체입니다."""

    SAY_DOWN = 1
    SAY_UP = -1
    SAY_CORRECT = 0

    def __init__(self, range_: int):
        self.range = range_
        self.number = randint(1, self.range)
        self.tries = 0

    def guess(self, guessing_number: int) -> int:
        """
        숫자를 예상합니다.
        :param guessing_number: 예상할 숫자
        :return: 이 숫자가 게임의 숫자보다 큰지 작은지 같은지
        """
        self.tries += 1
        if guessing_number > self.number:
            return UpdownGame.SAY_DOWN
        elif guessing_number < self.number:
            return UpdownGame.SAY_UP
        else:
            return UpdownGame.SAY_CORRECT

    @staticmethod
    def get_receive(tries: int, stake: float) -> float:
        return max((54 / tries - 4) / 5, 0) * stake


class EconomyCog(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.currency: str = strings()['currency']['terro']

    @commands.command(aliases=strings()['command']['money']['name'],
                      description=strings()['command']['money']['description'])
    async def money(self, ctx: Context):
        if account := EconomyManager.get_account(ctx.author.id):
            await ctx.send(strings()['command']['money']['strings']['template'].format(
                mention=ctx.author.mention, amount=account['property'], currency=self.currency))
        else:
            EconomyManager.new_account(ctx.author.id, force=True)
            await ctx.send(strings()['command']['money']['strings']['new_account'].format(
                mention=ctx.author.mention, currency=self.currency))

    @commands.group(aliases=strings()['command']['updown']['name'],
                    description=strings()['command']['updown']['description'],
                    invoke_without_command=True)
    async def updown(self, ctx: Context, stake: float = 10):
        account = EconomyManager.get_account(ctx.author.id)
        if not account:
            account = EconomyManager.new_account(ctx.author.id, force=True)
        if account['property'] < stake:
            await ctx.send(strings()['command']['updown']['strings']['not_enough_money'].format(
                mention=ctx.author.mention, stake=stake, currency=self.currency))
            return

        EconomyManager.give(ctx.author.id, -stake)

        await ctx.send(strings()['command']['updown']['strings']['range_notification'].format(
            mention=ctx.author.mention, stake=stake, currency=self.currency))

        game = UpdownGame(100)

        def check(message_: Message):
            return message_.channel == ctx.channel \
                   and message_.author == ctx.author \
                   and re.compile(r'\d+').match(message_.content)

        while True:
            try:
                message = await self.client.wait_for('message', timeout=60.0, check=check)
            except AsyncioTimeoutError:
                await ctx.send(strings()['command']['updown']['strings']['timeout'].format(
                    mention=ctx.author.mention, number=game.number))
                return

            guessing_number = int(message.content)
            state = game.guess(guessing_number)

            if state == UpdownGame.SAY_DOWN:
                await ctx.send(strings()['command']['updown']['strings']['number_is_big'].format(
                    mention=ctx.author.mention, number=guessing_number, tries=game.tries))
            elif state == UpdownGame.SAY_UP:
                await ctx.send(strings()['command']['updown']['strings']['number_is_small'].format(
                    mention=ctx.author.mention, number=guessing_number, tries=game.tries))
            else:
                times = UpdownGame.get_receive(game.tries, stake)
                amount = stake * times
                await ctx.send(strings()['command']['updown']['strings']['number_is_correct'].format(
                    mention=ctx.author.mention, tries=game.tries, times=times, amount=amount, currency=self.currency))
                EconomyManager.give(ctx.author.id, amount)
                return

    @updown.command(aliases=strings()['command']['updown.receive']['name'],
                    description=strings()['command']['updown.receive']['description'])
    async def updown_receive(self, ctx: Context, stake: float = 10):
        await ctx.send(strings()['command']['updown.receive']['strings']['template'].format(
            stake=stake, currency=self.currency,
            r1=UpdownGame.get_receive(1, stake), r2=UpdownGame.get_receive(2, stake),
            r3=UpdownGame.get_receive(3, stake), r4=UpdownGame.get_receive(4, stake),
            r5=UpdownGame.get_receive(5, stake), r6=UpdownGame.get_receive(6, stake),
            r7=UpdownGame.get_receive(7, stake)))


def setup(client: Bot):
    client.add_cog(EconomyCog(client))
