import re
from asyncio import TimeoutError as AsyncioTimeoutError, wait
from datetime import date, timedelta
from random import choice, randint
from typing import Optional

from discord import Message, Member, Embed, VoiceChannel
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context, MemberConverter, MemberNotFound

from manager import TypingManager, TypingGame, BabelManager, AttendanceManager, Dice
from util import datetime, get_keys, get_strings, get_const


def strings():
    return get_strings()['cog']['extraessential']


class ExtraessentialCog(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.typing_manager = TypingManager()

    @tasks.loop(seconds=600.0)
    async def babel_upper(self):
        print('gooder')
        for channel in self.client.get_guild(get_const()['guild']['shtelo']).voice_channels:
            for member in channel.members:
                BabelManager.up(member, len(channel.members))

    @tasks.loop(seconds=3000.0)
    async def babel_upper(self):
        print('good')
        for leader in BabelManager.get_leaderboard():
            BabelManager.up(leader['member_id'], -3)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceChannel, after: VoiceChannel):
        if after is None:
            if before is not None:
                BabelManager.up(member.id, -len(before.members) * 3)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.content.startswith(strings()['magic_conch']['strings']['invoker']):
            """마법의 소라고둥 (`magic_conch`)"""
            answer = choice(strings()['magic_conch']['strings']['answers'])
            await message.channel.send(strings()['magic_conch']['strings']['template'].format(message=answer))

        if re.compile(r'(.|\n)*\?\d+').match(message.content):
            """`vote_reaction`"""
            for i in range(min(int(message.content.split('?')[-1]), 20)):
                await message.add_reaction(strings()['vote_reaction']['strings']['emojis'][i])

        if not message.author.bot:
            BabelManager.up(message.author.id, len(message.content) // 30)

    @commands.command(aliases=strings()['command']['dice']['name'],
                      description=strings()['command']['dice']['description'])
    async def dice(self, ctx: Context, dice: Dice):
        if dice is None:
            await ctx.send(strings()['command']['dice']['strings']['no_dice'])
            return
        elif dice.count > 1000:
            await ctx.send(strings()['command']['dice']['strings']['too_many_dice'])
            return

        await ctx.send(strings()['command']['dice']['strings']['template'].format(dice=dice, number=dice.roll()))

    @commands.command(aliases=strings()['command']['random']['name'],
                      description=strings()['command']['random']['description'])
    async def random(self, ctx: Context, lower_limit: int = 100, upper_limit: Optional[int] = None):
        if upper_limit is None:
            lower_limit, upper_limit = 1, lower_limit
        if lower_limit > upper_limit:
            lower_limit, upper_limit = upper_limit, lower_limit

        number = randint(lower_limit, upper_limit)

        percent = round((number - lower_limit) / (upper_limit - lower_limit) * 100000) / 1000
        await ctx.send(strings()['command']['random']['strings']['template'].format(number=number, percent=percent))

    @commands.group(aliases=strings()['command']['typing']['name'],
                    description=strings()['command']['typing']['description'],
                    invoke_without_command=True)
    async def typing(self, ctx: Context, language: str = TypingManager.LANGUAGE_CODE_REVERSED[TypingManager.KOREAN]):
        if ctx.channel.id in self.typing_manager.games:
            await ctx.send(strings()['command']['typing']['strings']['already_gaming'])
            return
        if re.compile(r'\d+').match(language):
            sentence = TypingManager.get_sentence_by_id(int(language))
            language = TypingManager.LANGUAGE_CODE_REVERSED[sentence['language']]
        else:
            if language not in TypingManager.LANGUAGE_CODE.keys():
                await ctx.send(strings()['command']['typing']['strings']['invalid_language'].format(
                    languages='`' + '`, `'.join(TypingManager.LANGUAGE_CODE_REVERSED.values()) + '`'
                ))
                return
            elif language == TypingManager.LANGUAGE_CODE_REVERSED[TypingManager.JAPANESE]:
                await ctx.send(strings()['command']['typing']['strings']['japanese_not_supported'])
                return

            if language == TypingManager.LANGUAGE_CODE_REVERSED[TypingManager.KOREAN]:
                sentence = TypingManager.get_sentence(TypingManager.KOREAN)
            else:
                sentence = TypingManager.get_sentence(TypingManager.ENGLISH)

        game = TypingGame(ctx.channel, (sentence['content'], sentence['id']))

        self.typing_manager.add_game(game)

        def check(self_, message_: Message):
            return message_.channel == game.channel and message_.author.id != self_.client.user.id

        while True:
            game.message = await ctx.send(strings()['command']['typing']['strings']['template'].format(
                keys=game.keys, sentence=TypingManager.acheatablify(game.sentence), id=game.sentence_id))
            try:
                message = await self.client.wait_for('message', check=lambda *x: check(self, *x), timeout=game.keys)
            except AsyncioTimeoutError:
                await ctx.send(strings()['command']['typing']['strings']['timeout'])
            else:
                if message.content == game.sentence:
                    break
                else:
                    await game.message.delete()

        seconds, speed = game.calculate(datetime.now())
        await ctx.send(strings()['command']['typing']['strings']['succeed'].format(
            mention=message.author.mention, seconds=seconds, speed=speed))

        self.typing_manager.check_and_record(message.author.id, TypingManager.LANGUAGE_CODE[language], speed)
        del self.typing_manager.games[ctx.channel.id]

    @typing.command(aliases=strings()['command']['typing.add']['name'],
                    description=strings()['command']['typing.add']['description'])
    async def typing_add(self, ctx: Context, language: str, *, sentence: str):
        if language not in TypingManager.LANGUAGE_CODE.keys():
            await ctx.send(strings()['command']['typing.add']['strings']['invalid_language'].format(
                language='`' + '`, `'.join(TypingManager.LANGUAGE_CODE.keys()) + '`'))
            return

        message = await ctx.send(strings()['command']['typing.add']['strings']['wanna_commit'].format(
            language=language, sentence=sentence, keys=get_keys(sentence)))
        await wait((message.add_reaction(get_strings()['emoji']['x']),
                    message.add_reaction(get_strings()['emoji']['o'])))

        def check(reaction_, user_):
            return user_ == ctx.author and reaction_.emoji in (
                get_strings()['emoji']['x'], get_strings()['emoji']['o'])

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
        except AsyncioTimeoutError:
            await message.edit(content=strings()['command']['typing.add']['strings']['timeout'])
        else:
            if reaction.emoji == get_strings()['emoji']['o']:
                if db_sentence := TypingManager.get_sentence_by_content(sentence):
                    await message.edit(content=strings()['command']['typing.add']['strings']['duplicated'].format(
                        id=db_sentence['id']))
                else:
                    id_ = TypingManager.add_sentence(TypingManager.LANGUAGE_CODE[language], sentence)
                    await message.edit(content=strings()['command']['typing.add']['strings']['succeed'].format(id=id_))
            else:
                await message.edit(content=strings()['command']['typing.add']['strings']['cancelled'])

        await message.clear_reactions()

    @typing.command(aliases=strings()['command']['typing.edit']['name'],
                    description=strings()['command']['typing.edit']['description'])
    async def typing_edit(self, ctx: Context, sentence_id: int, *, sentence: str):
        if not (db_sentence := TypingManager.get_sentence_by_id(sentence_id)):
            await ctx.send(strings()['command']['typing.edit']['strings']['no_sentence'].format(id=sentence_id))
            return

        message = await ctx.send(strings()['command']['typing.edit']['strings']['wanna_change'].format(
            id=sentence_id, before=db_sentence['content'], after=sentence
        ))
        await wait((message.add_reaction(get_strings()['emoji']['o']),
                    message.add_reaction(get_strings()['emoji']['x'])))

        def check(reaction_, user_):
            return user_ == ctx.author and reaction_.emoji in (get_strings()['emoji']['o'],
                                                               get_strings()['emoji']['x'])

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60.0)
        except AsyncioTimeoutError:
            await message.edit(content=strings()['command']['typing.edit']['strings']['timeout'])
        else:
            if reaction.emoji == get_strings()['emoji']['o']:
                TypingManager.update_sentence(sentence_id, sentence)
                await message.edit(content=strings()['command']['typing.edit']['strings']['succeed'])
            else:
                await message.edit(content=strings()['command']['typing.edit']['strings']['cancelled'])
            await message.clear_reactions()

    @typing.command(aliases=strings()['command']['typing.records']['name'],
                    description=strings()['command']['typing.records']['description'])
    async def typing_records(self, ctx: Context, language: Optional[str] = None, limit: int = 20):
        if language in TypingManager.LANGUAGE_CODE.keys():
            language = TypingManager.LANGUAGE_CODE[language]
        else:
            language = -1
        records = TypingManager.get_records_ordered(limit, language)
        contents = []
        member_converter = MemberConverter()
        for i, record in enumerate(records):
            try:
                member = await member_converter.convert(ctx, record['author'])
            except MemberNotFound:
                TypingManager.delete_record(record['author'])
                continue
            contents.append(strings()['command']['typing.records']['strings']['line_template'].format(
                order=i + 1, member=member.display_name,
                language=TypingManager.LANGUAGE_CODE_REVERSED[record['language']], record=record['record']))

        await ctx.send(strings()['command']['typing.records']['strings']['template'].format(data='\n> '.join(contents)))

    @commands.group(aliases=strings()['command']['attendance']['name'],
                    description=strings()['command']['attendance']['description'])
    async def attendance(self, ctx: Context):
        if ctx.invoked_subcommand is not None:
            return

        strike = AttendanceManager.attend(ctx.author.id)
        BabelManager.up(ctx.author.id, 10)
        await ctx.send(strings()['command']['attendance']['strings']['template'].format(
            name=ctx.author.display_name, strike=strike))

    @attendance.command(aliases=strings()['command']['attendance.check']['name'],
                        description=strings()['command']['attendance.check']['description'])
    async def attendance_check(self, ctx: Context, member: Optional[Member] = None):
        if member is None:
            member = ctx.author
        attendance = AttendanceManager.get_attendance(member.id)

        yesterday = date.today() - timedelta(days=1)

        if not attendance or attendance['date'] < yesterday:
            await ctx.send(strings()['command']['attendance.check']['strings']['no_data'].format(
                name=member.display_name))
        elif attendance['date'] == yesterday:
            await ctx.send(strings()['command']['attendance.check']['strings']['yesterday'].format(
                name=member.display_name, strike=attendance['strike']))
        else:
            await ctx.send(strings()['command']['attendance.check']['strings']['today'].format(
                name=member.display_name, strike=attendance['strike']))

    @commands.group(aliases=strings()['command']['babel']['name'],
                    description=strings()['command']['babel']['description'])
    async def babel(self, ctx: Context):
        leaderboard = BabelManager.get_leaderboard()
        if leaderboard:
            description = []
            for i, leader in enumerate(leaderboard):
                floor = leader['floor']
                member = await MemberConverter().convert(ctx, leader['member_id'])
                description.append(strings()['command']['babel']['strings']['template'].format(
                    place=i + 1, display_name=member.display_name, floor=floor))
            description = '\n'.join(description)
        else:
            description = strings()['command']['babel']['strings']['no_leaderboard']
        embed = Embed(title='바벨', description=description, colour=get_const()['color']['sch_vanilla'])
        await ctx.send(embed=embed)

    @babel.command(aliases=strings()['command']['babel.condition']['name'],
                   description=strings()['command']['babel.condition']['description'])
    async def babel_condition(self, ctx: Context):
        embed = Embed(title=strings()['command']['babel.condition']['strings']['title'],
                      colour=get_const()['color']['sch_vanilla'])
        embed.add_field(name=strings()['command']['babel.condition']['strings']['up'],
                        value=strings()['command']['babel.condition']['strings']['up_condition'])
        embed.add_field(name=strings()['command']['babel.condition']['strings']['down'],
                        value=strings()['command']['babel.condition']['strings']['down_condition'])
        await ctx.send(embed=embed)


def setup(client: Bot):
    client.add_cog(ExtraessentialCog(client))
