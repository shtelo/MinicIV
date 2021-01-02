import re
from asyncio import TimeoutError as AsyncioTimeoutError, wait, sleep
from datetime import date, timedelta, datetime
from random import choice, randint
from typing import Optional

from discord import Message, Member, Embed, VoiceChannel, Guild, Game
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context, MemberNotFound

from manager import TypingManager, TypingGame, BabelManager, AttendanceManager, Dice, EmojiReactionManager, \
    MemoManager, EconomyManager
from manager.member_cache import MemberCache
from util import get_keys, get_strings, get_const
from util.postposition import i_ga


def strings():
    return get_strings()['cog']['extraessential']


class ExtraessentialCog(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.typing_manager = TypingManager()
        self.babel_buffer = dict()
        self.shtelo_guild: Optional[Guild] = None
        self.emoji_reaction_manager = EmojiReactionManager()
        self.member_cache = MemberCache()
        self.activity_names = [
            lambda: f'{AttendanceManager.get_length()}명이 출석',
            lambda: f'{BabelManager.get_leaders_length()}명이 바벨 등반',
            lambda: f'{EmojiReactionManager.get_length()}개의 반응',
            lambda: f'{MemoManager.get_length()}개 메모',
            lambda: f'{TypingManager.get_leaders_length()}개의 타자연습 기록',
            lambda: f'{TypingManager.get_sentences_length()}개 문장 타자연습',
            lambda: f'{EconomyManager.get_length()}개 계좌 관리',
            lambda: f'{self.member_cache.get_length()}명 기억'
        ]

        self.activity_switcher.start()
        self.babel_upper.start()
        self.babel_gravity.start()

    def cog_unload(self):
        self.babel_upper.cancel()
        self.babel_gravity.cancel()

    @tasks.loop(seconds=30.0)
    async def activity_switcher(self):
        while self.shtelo_guild is None:
            await sleep(1)
        name = self.activity_names[0]()
        await self.client.change_presence(activity=Game(name))
        self.activity_names = self.activity_names[1:] + self.activity_names[:1]

    @tasks.loop(seconds=600.0)
    async def babel_upper(self):
        while not self.shtelo_guild:
            await sleep(1)
        for channel in self.shtelo_guild.voice_channels:
            member_ids = channel.voice_states.keys()
            for member_id in member_ids:
                BabelManager.up(member_id, len(member_ids))

    @tasks.loop(seconds=3000.0)
    async def babel_gravity(self):
        for leader in BabelManager.get_leaderboard():
            BabelManager.up(leader['member_id'], -3)

    @commands.Cog.listener()
    async def on_ready(self):
        self.shtelo_guild = self.client.get_guild(get_const()['guild']['shtelo'])

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """마법의 소라고둥 (`magic_conch`)"""
        if message.content.startswith(strings()['magic_conch']['strings']['invoker']):
            answer = choice(strings()['magic_conch']['strings']['answers'])
            await message.channel.send(strings()['magic_conch']['strings']['template'].format(message=answer))

        """vote reaction"""
        if re.compile(r'(.|\n)*\?\d+').match(message.content):
            for i in range(min(int(message.content.split('?')[-1]), 20)):
                await message.add_reaction(strings()['vote_reaction']['strings']['emojis'][i])

        """babel"""
        if not message.author.bot:
            if message.author.id not in self.babel_buffer:
                self.babel_buffer[message.author.id] = 0
            self.babel_buffer[message.author.id] += len(message.content)
            if self.babel_buffer[message.author.id] >= 30:
                quotient = self.babel_buffer[message.author.id] // 30
                self.babel_buffer[message.author.id] %= 30
                BabelManager.up(message.author.id, quotient)

        """emoji reactions"""
        if reactions := self.emoji_reaction_manager.get_reactions(message.content):
            tasks_ = list()
            for reaction in reactions:
                tasks_.append(message.add_reaction(reaction))
            await wait(tasks_)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceChannel, after: VoiceChannel):
        if after is None:
            if before is not None:
                BabelManager.up(member.id, -len(before.members) * 3)

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
        for i, record in enumerate(records):
            try:
                member = await self.member_cache.get_member(record['author'], ctx)
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

    @attendance.command(aliases=strings()['command']['attendance.leaderboard']['name'],
                        description=strings()['command']['attendance.leaderboard']['description'])
    async def attendance_leaderboard(self, ctx: Context):
        description = []
        for i, leader in enumerate(AttendanceManager.get_leaderboard()):
            member_id, strike, date_ = leader
            description.append(strings()['command']['attendance.leaderboard']['strings']['template'].format(
                place=i + 1, member=(await self.member_cache.get_member(member_id, ctx)).display_name, strike=strike,
                did_today=':fire:' if date_ == date.today() else ''))
        embed = Embed(title=strings()['command']['attendance.leaderboard']['strings']['embed_title'],
                      description='\n'.join(description), colour=get_const()['color']['sch_vanilla'])
        await ctx.send(embed=embed)

    @commands.group(aliases=strings()['command']['babel']['name'],
                    description=strings()['command']['babel']['description'],
                    invoke_without_command=True)
    async def babel(self, ctx: Context):
        leaderboard = BabelManager.get_leaderboard()
        if leaderboard:
            description = []
            for i, leader in enumerate(leaderboard):
                floor = leader['floor']
                member = await self.member_cache.get_member(leader['member_id'], ctx)
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

    @commands.group(aliases=strings()['command']['emoji_reaction']['name'],
                    description=strings()['command']['emoji_reaction']['description'],
                    invoke_without_command=True)
    async def emoji_reaction(self, ctx: Context):
        await self.emoji_reaction_list(ctx)

    @emoji_reaction.command(aliases=strings()['command']['emoji_reaction.list']['name'],
                            description=strings()['command']['emoji_reaction.list']['description'])
    async def emoji_reaction_list(self, ctx: Context):
        embed = Embed(title=strings()['command']['emoji_reaction.list']['strings']['embed_title'],
                      color=get_const()['color']['sch_vanilla'])
        i = 0
        for emoji, reactions in self.emoji_reaction_manager.reactions.items():
            if i >= 20:
                break
            embed.add_field(name=emoji,
                            value='`' + '`, `'.join(reactions) + '`')
            i += 1
        await ctx.send(embed=embed)

    @emoji_reaction.command(aliases=strings()['command']['emoji_reaction.add']['name'],
                            description=strings()['command']['emoji_reaction.add']['description'])
    async def emoji_reaction_add(self, ctx: Context, emoji_unicode: str, *, keyword: str):
        if self.emoji_reaction_manager.is_reaction(emoji_unicode, keyword):
            await ctx.send(strings()['command']['emoji_reaction.add']['strings']['duplicated'])
            return

        self.emoji_reaction_manager.add_reaction(emoji_unicode, keyword)
        await ctx.send(strings()['command']['emoji_reaction.add']['strings']['succeed'].format(
            keyword=keyword, emoji=emoji_unicode))

    @emoji_reaction.command(aliases=strings()['command']['emoji_reaction.remove']['name'],
                            description=strings()['command']['emoji_reaction.remove']['description'])
    async def emoji_reaction_remove(self, ctx: Context, emoji_unicode: str, *, keyword: str):
        if not self.emoji_reaction_manager.is_reaction(emoji_unicode, keyword):
            await ctx.send(strings()['command']['emoji_reaction.remove']['strings']['no_reaction'].format(
                keyword=keyword, emoji=emoji_unicode))
            return

        self.emoji_reaction_manager.remove_reaction(emoji_unicode, keyword)
        await ctx.send(strings()['command']['emoji_reaction.remove']['strings']['succeed'].format(
            keyword=keyword, emoji=emoji_unicode, i_ga=i_ga(keyword)))

    @emoji_reaction.command(aliases=strings()['command']['emoji_reaction.refresh']['name'],
                            description=strings()['command']['emoji_reaction.refresh']['description'])
    async def emoji_reaction_refresh(self, ctx: Context):
        map_ = self.emoji_reaction_manager.refresh_reactions()
        count = 0
        for reactions in map_.values():
            count += len(reactions)
        await ctx.send(strings()['command']['emoji_reaction.refresh']['strings']['succeed'].format(count=count))


def setup(client: Bot):
    client.add_cog(ExtraessentialCog(client))
