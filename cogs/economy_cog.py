import re
from asyncio import TimeoutError as AsyncioTimeoutError

from discord import Message, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from manager import EconomyManager, UpdownGame, MemberCache
from util import get_strings, get_const


def strings():
    return get_strings()['cog']['economy']


class Economy(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.member_cache = MemberCache()
        self.currency: str = strings()['currency']['terro']

    @commands.group(aliases=strings()['command']['money']['name'],
                    description=strings()['command']['money']['description'],
                    invoke_without_command=True)
    async def money(self, ctx: Context):
        if account := EconomyManager.get_account(ctx.author.id):
            await ctx.send(strings()['command']['money']['strings']['template'].format(
                mention=ctx.author.mention, amount=account['property'], currency=self.currency))
        else:
            EconomyManager.new_account(ctx.author.id, force=True)
            await ctx.send(strings()['command']['money']['strings']['new_account'].format(
                mention=ctx.author.mention, currency=self.currency))

    @money.command(aliases=strings()['command']['money.list']['name'],
                   description=strings()['command']['money.list']['description'])
    async def money_list(self, ctx: Context, limit: int = 15):
        leaderboard = EconomyManager.get_leaderboard(limit)

        contents = list()

        for i, leader_info in enumerate(leaderboard):
            leader = await self.member_cache.get_member(leader_info['id'], ctx)
            contents.append(strings()['command']['money.list']['strings']['template'].format(
                index=i+1, name=leader.display_name, amount=leader_info['property'], currency=self.currency))

        await ctx.send(embed=Embed(title=strings()['command']['money.list']['strings']['embed_title'],
                                   description='\n'.join(contents), colour=get_const()['color']['sch_vanilla']))

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
                times = UpdownGame.get_receive(game.tries)
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
            r1=UpdownGame.get_receive(1) * stake, r2=UpdownGame.get_receive(2) * stake,
            r3=UpdownGame.get_receive(3) * stake, r4=UpdownGame.get_receive(4) * stake,
            r5=UpdownGame.get_receive(5) * stake, r6=UpdownGame.get_receive(6) * stake,
            r7=UpdownGame.get_receive(7) * stake))


def setup(client: Bot):
    client.add_cog(Economy(client))
