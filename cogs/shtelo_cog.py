from asyncio import wait
from datetime import timedelta, datetime

from discord import Member, Embed, Message, Guild
from discord.ext import commands
from discord.ext.commands import Bot, Context, MemberConverter

from manager import WeekDay, ShteloTime, AnnouncementManager
from util import get_strings, get_const


def strings():
    return get_strings()['cog']['shtelo']


class Shtelo(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.announcement_manager = AnnouncementManager(self.client)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if self.announcement_manager.channel is None:
            self.announcement_manager.channel = self.client.get_channel(get_const()['channel']['central_park'])
        if message.channel == self.announcement_manager.channel:
            await self.announcement_manager.tick()

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
        reactions = list()
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

    @commands.group(aliases=strings()['command']['announcement']['name'],
                    description=strings()['command']['announcement']['description'],
                    invoke_without_command=True)
    async def announcement(self, ctx: Context):
        await self.announcement_manager.tick()
        await ctx.send(strings()['command']['announcement']['strings']['template'].format(
            cool_message=self.announcement_manager.cool_message))

    @announcement.command(aliases=strings()['command']['announcement.add']['name'],
                          description=strings()['command']['announcement.add']['description'])
    @commands.has_role('파트너')
    async def announcement_add(self, ctx: Context, *, string: str):
        AnnouncementManager.add_announcement(string)
        await ctx.send(strings()['command']['announcement.add']['strings']['succeed'].format(string=string))
        self.announcement_manager.refresh_announcements()

    @announcement.command(aliases=strings()['command']['announcement.list']['name'],
                          description=strings()['command']['announcement.list']['description'])
    async def announcement_list(self, ctx: Context):
        content = list()

        for announcement in AnnouncementManager.get_announcements():
            id_ = announcement['id']
            string = announcement['string']
            content.append(strings()['command']['announcement.list']['strings']['template'].format(
                string=string, id=id_))
        await ctx.send('\n'.join(content))
        self.announcement_manager.refresh_announcements()

    @announcement.command(aliases=strings()['command']['announcement.delete']['name'],
                          description=strings()['command']['announcement.delete']['description'])
    @commands.has_role('파트너')
    async def announcement_delete(self, ctx: Context, id_: int):
        announcement = AnnouncementManager.get_announcement(id_)
        AnnouncementManager.delete_announcement(id_)
        await ctx.send(strings()['command']['announcement.delete']['strings']['succeed'].format(
            string=announcement['string'], id=id_))
        self.announcement_manager.refresh_announcements()

    @commands.command(aliases=strings()['command']['member_list']['name'],
                      description=strings()['command']['member_list']['description'])
    async def member_list(self, ctx: Context):
        await ctx.send(strings()['command']['member_list']['strings']['link'])

    @commands.command(aliases=strings()['command']['conversation_list']['name'],
                      description=strings()['command']['conversation_list']['description'])
    async def conversation_list(self, ctx: Context):
        await ctx.send(strings()['command']['conversation_list']['strings']['link'])

    @commands.command(aliases=strings()['command']['admit']['name'],
                      description=strings()['command']['admit']['description'])
    @commands.has_role('파트너')
    async def admit(self, ctx: Context, member: Member):
        tester_role = ctx.guild.get_role(get_const()['role']['tester'])
        partner_role = ctx.guild.get_role(get_const()['role']['partner'])
        separator_entitle_role = ctx.guild.get_role(get_const()['role']['separator_entitle'])
        separator_deck_role = ctx.guild.get_role(get_const()['role']['separator_deck'])
        partners_text_channel = ctx.guild.get_channel(get_const()['channel']['partners'])

        await wait((
            ctx.send(strings()['command']['admit']['strings']['template'].format(
                member=member.mention)),
            ctx.message.add_reaction(get_const()['emoji']['white_check_mark']),
            member.add_roles(tester_role, separator_entitle_role, separator_deck_role),
            partners_text_channel.send(strings()['command']['admit']['strings']['for_partners'].format(
                member=member.mention, partners_mention=partner_role.mention
            ))
        ))


def setup(client: Bot):
    client.add_cog(Shtelo(client))
