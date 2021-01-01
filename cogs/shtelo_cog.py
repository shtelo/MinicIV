from asyncio import wait
from datetime import timedelta, datetime

from discord import Member, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from manager import WeekDay, ShteloTime
from util import get_strings, get_const


def strings():
    return get_strings()['cog']['shtelo']


class ShteloCog(commands.Cog):
    @commands.command(aliases=strings()['command']['administrator_vote']['name'],
                      description=strings()['command']['administrator_vote']['description'])
    async def administrator_vote(self, ctx: Context, *members: Member):
        embed = Embed(
            title=strings()['command']['administrator_vote']['strings']['administrator_election'],
            description=strings()['command']['administrator_vote']['strings']['embed_description'].format(
                datetime=datetime.now() + timedelta(days=7)),
            colour=get_const()['color']['sch_vanilla'])
        embed.set_thumbnail(url=ctx.guild.icon_url)
        emojis = strings()['command']['administrator_vote']['emojis']
        reactions = []
        for i, member in enumerate(members):
            embed.add_field(name=emojis[i], value=member.mention)
            reactions.append(emojis[i])
        message = await ctx.send(embed=embed)
        await wait([message.add_reaction(reaction) for reaction in reactions])

    @commands.group(aliases=strings()['command']['shtelian_calendar']['name'],
                    description=strings()['command']['shtelian_calendar']['description'])
    async def shtelian_calendar(self, ctx: Context, *args):
        if not args:
            await ctx.send(str(ShteloTime.by_datetime(datetime.today())))
            return
        try:
            await self.to_shtelian_calendar(ctx, *args)
        except ValueError:
            await self.from_shtelian_calendar(ctx, args[0], args[1], await WeekDay().convert(ctx, args[2]))

    @shtelian_calendar.command()
    async def to_shtelian_calendar(self, ctx: Context, year: str, month: str, day: str):
        year = int(year[:-1] if year.endswith('년') else year)
        month = int(month[:-1] if month.endswith('월') else month)
        day = int(day[:-1] if day.endswith('일') else day)
        if date := ShteloTime.by_datetime(datetime(year, month, day)):
            await ctx.send(str(date))
        else:
            await ctx.send(strings()['command']['shtelian_calendar']['strings']['no_shtelo'])

    @shtelian_calendar.command()
    async def from_shtelian_calendar(self, ctx: Context, term_number: str, week: str, week_day: WeekDay):
        term_number = int(term_number[:-1] if term_number.endswith('기') else term_number)
        week = int(week[:-1] if week.endswith('주') else week)
        try:
            date = ShteloTime(term_number, week, week_day).convert()
        except ValueError:
            await ctx.send(strings()['command']['shtelian_calendar']['strings']['invalid_date'])
        else:
            await ctx.send(strings()['command']['shtelian_calendar']['strings']['date'].format(
                year=date.year, month=date.month, day=date.day))


def setup(client: Bot):
    client.add_cog(ShteloCog(client))
