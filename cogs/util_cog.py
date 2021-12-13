from asyncio import wait, TimeoutError as AsyncioTimeoutError, sleep
from datetime import datetime
from typing import Optional

from discord import VoiceChannel, Message, TextChannel, Embed
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context, CommandNotFound, CommandError, TextChannelConverter, Command

from cogs.shtelo.bot_protocol import BotProtocol, Request
from manager import Memo, MemoManager, DatetimeConverter, MusicCache, LanguageName, MemberCache
from manager.language import LANGUAGE_UNKNOWN
from util import load_strings, get_strings, get_const
from util.naver_api import language_detect, translate, TRANSLATABLES
from util.postposition import euro, eul_reul, i_ga, a_ya, eun_neun
from zasok_datetime import ZasokDatetime


def strings():
    return get_strings()['cog']['util']


class MinicProtocol(BotProtocol):
    async def on_echo(self, request: Request):
        if request.addition:
            await request.message.channel.send(request.addition)

    async def on_pass(self, request: Request):
        command_prefix, channel, message = request.addition.split(' ', 2)
        request_ctx = await self.client.get_context(request.message)
        channel = await TextChannelConverter().convert(request_ctx, channel)
        message = await channel.fetch_message(int(message))
        ctx = await self.client.get_context(message)
        self.client.command_prefix.insert(0, command_prefix)
        await self.client.invoke(ctx)
        self.client.command_prefix.remove(command_prefix)


class Util(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.bot_protocol = MinicProtocol(self.client)
        self.member_cache = MemberCache()
        self.music_cache = MusicCache()

        self.optimize_cache.start()

    @tasks.loop(seconds=1800.0)
    async def optimize_cache(self):
        self.member_cache.optimize_cache()
        self.music_cache.optimize_cache()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        await self.bot_protocol.on_message(message)

        if isinstance(message.channel, TextChannel):
            print(get_strings()['message_log_template'].format(
                datetime=datetime.now(), guild=message.guild, guild_id=message.guild.id,
                channel=message.channel, channel_id=message.channel.id,
                author=message.author, author_id=message.author.id, content=message.content))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, CommandNotFound):
            await ctx.send(f'ALL PASS $ {ctx.channel.mention} {ctx.message.id}')
        else:
            await ctx.send(f'<@!366565792910671873> 오류가 발생했습니다.\n> ||{error}||')

    # noinspection PyUnusedLocal
    @commands.command(aliases=strings()['command']['move']['name'],
                      description=strings()['command']['move']['description'])
    async def move(self, ctx: Context, from_channel: VoiceChannel, to_channel: VoiceChannel):
        tasks_ = list()
        for member_id in from_channel.voice_states.keys():
            tasks_.append((await self.member_cache.get_member(member_id, ctx)).edit(voice_channel=to_channel))
        await wait(tasks_)

    @commands.command(aliases=strings()['command']['gather']['name'],
                      description=strings()['command']['gather']['description'])
    async def gather(self, ctx: Context, to_channel_id: int = 0):
        if not to_channel_id:
            destination_channel = ctx.message.author.voice.channel
            if destination_channel is None:
                await ctx.send(strings()['command']['gather']['strings']['no_channel_found'])
                return
        else:
            destination_channel = ctx.guild.get_channel(to_channel_id)
            if destination_channel is None:
                await ctx.send(strings()['command']['gather']['strings']['invalid_id'])
                return

        tasks_ = list()
        for voice_channel in ctx.guild.voice_channels:
            if voice_channel.id not in (ctx.guild.afk_channel.id, destination_channel.id):
                for member in voice_channel.members:
                    tasks_.append(member.edit(voice_channel=destination_channel))

        await wait(tasks_)

    @commands.group(aliases=strings()['command']['memo']['name'],
                    description=strings()['command']['memo']['description'],
                    invoke_without_command=True)
    async def memo(self, ctx: Context, key: Optional[str] = None):
        if key is None:
            await self.memo_list(ctx)
            return
        if MemoManager.is_key(key):
            await ctx.send(strings()['command']['memo']['strings']['template']
                           .format(data=MemoManager.get_value(key).replace('\n', '\n> ')))
        else:
            await ctx.send(strings()['command']['memo']['strings']['invalid_key']
                           .format(key=key, eul_reul=eul_reul(key)))

    @memo.command(aliases=strings()['command']['memo.set']['name'],
                  description=strings()['command']['memo.set']['description'])
    async def memo_set(self, ctx: Context, key: str, *, value: str):
        completed_content = strings()['command']['memo.set']['strings']['template'] \
            .format(key=key, eul_reul=eul_reul(key), value=value)

        if MemoManager.is_key(key):
            if MemoManager.get_author_id(key) != ctx.author.id:
                await ctx.send(strings()['command']['memo.set']['strings']['permission_denied'])
                return

            message = await ctx.send(strings()['command']['memo.set']['strings']['duplicated']
                                     .format(key=key, euro=euro(key)))
            await wait((message.add_reaction(get_strings()['emoji']['o']),
                        message.add_reaction(get_strings()['emoji']['x'])))

            def check(reaction_, user_):
                return reaction_.emoji in (get_strings()['emoji']['o'], get_strings()['emoji']['x']) and \
                       user_ == ctx.message.author

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
            except AsyncioTimeoutError:
                await message.edit(content=strings()['command']['memo.set']['strings']['timeout'])
                return
            else:
                if reaction.emoji == get_strings()['emoji']['x']:
                    await message.edit(content=strings()['command']['memo.set']['strings']['cancelled'])
                    return

            await wait((message.edit(content=completed_content), message.clear_reactions()))
            MemoManager.update(key, Memo(value, ctx.message.author.id))

        else:
            await ctx.send(completed_content)
            MemoManager.insert(key, Memo(value, ctx.message.author.id))

    @memo.command(aliases=strings()['command']['memo.list']['name'],
                  description=strings()['command']['memo.list']['description'])
    async def memo_list(self, ctx: Context):
        if keys := MemoManager.get_keys():
            memos = '`' + '`, `'.join(keys) + '`'
            content = strings()['command']['memo.list']['strings']['template'].format(count=len(keys), memos=memos)
        else:
            content = strings()['command']['memo.list']['strings']['no_memo']

        await ctx.send(content)

    @memo.command(aliases=strings()['command']['memo.delete']['name'],
                  description=strings()['command']['memo.delete']['description'])
    async def memo_delete(self, ctx: Context, key: str):
        if not MemoManager.is_key(key):
            await ctx.send(strings()['command']['memo.delete']['strings']['no_memo'])
            return

        if ctx.author.id == MemoManager.get_author_id(key):
            MemoManager.delete(key)
            await ctx.send(strings()['command']['memo.delete']['strings']['delete'].format(key=key, i_ga=i_ga(key)))
        else:
            await ctx.send(strings()['command']['memo.delete']['strings']['permission_denied'])

    @commands.command(aliases=strings()['command']['reload_strings']['name'],
                      description=strings()['command']['reload_strings']['description'])
    async def reload_strings(self, ctx: Context):
        load_strings()
        await ctx.send(strings()['command']['reload_strings']['strings']['succeed'])

    @commands.command(aliases=strings()['command']['raw_string']['name'],
                      description=strings()['command']['raw_string']['description'])
    async def raw_string(self, ctx: Context, *, sentence: str):
        sentence = ''.join(map(lambda x: '\\' + x, list(sentence)))
        await ctx.send(strings()['command']['raw_string']['strings']['template'].format(value=sentence))

    @commands.command(aliases=strings()['command']['postposition']['name'],
                      description=strings()['command']['postposition']['description'])
    async def postposition(self, ctx: Context, *, words: str):
        await ctx.send(strings()['command']['postposition']['strings']['template'].format(
            words=words, a_ya=a_ya(words), i_ga=i_ga(words), eun_neun=eun_neun(words), euro=euro(words),
            eul_reul=eul_reul(words)))

    # noinspection PyUnusedLocal
    @commands.command(aliases=strings()['command']['cookie']['name'],
                      description=strings()['command']['cookie']['description'])
    async def cookie(self, ctx: Context, *string: str):
        await ctx.send(strings()['command']['cookie']['strings']['template'].format(latency=self.client.latency * 1000))

    @commands.command(aliases=strings()['command']['notify']['name'],
                      description=strings()['command']['notify']['description'])
    async def notify(self, ctx: Context, target: DatetimeConverter, *,
                     content: str = strings()['command']['notify']['strings']['default_notification']):
        target: datetime
        delta = target - datetime.now()
        delta = delta.days * 86400 + delta.seconds
        minutes, seconds = delta // 60, delta % 60
        hours, minutes = minutes // 60, minutes % 60
        await ctx.send(strings()['command']['notify']['strings']['template'].format(
            hours=hours, minutes=minutes, seconds=seconds, datetime=target, content=content))
        message_content = strings()['command']['notify']['strings']['notify'].format(
            mention=ctx.author.mention, content=content)
        tasks_ = (ctx.send(message_content), ctx.author.send(message_content))
        await sleep(delta)
        await wait(tasks_)

    @commands.command(aliases=strings()['command']['translate']['name'],
                      description=strings()['command']['translate']['description'])
    async def translate(self, ctx: Context, target_language: LanguageName, *, content: str):
        if target_language == LANGUAGE_UNKNOWN:
            await ctx.send(strings()['command']['translate']['strings']['target_language_unknown'])
            return
        elif (source_language := language_detect(content)) not in TRANSLATABLES:
            languages = '`' + '`, `'.join(str(language) for language in TRANSLATABLES.keys()) + '`'
            await ctx.send(strings()['command']['translate']['strings']['source_language_unknown'].format(
                languages=languages, eul_reul=eul_reul(languages[-2])))
            return
        elif target_language not in (languages := TRANSLATABLES[source_language]):
            languages = '`' + '`, `'.join(str(language) for language in languages) + '`'
            await ctx.send(strings()['command']['translate']['strings']['translation_unavailable'].format(
                source_language=source_language, eun_neun=eun_neun(str(source_language)),
                target_language=target_language, euro=euro(str(target_language)),
                eul_reul=eul_reul(str(source_language)), languages=languages))
            return

        translated = translate(source_language, target_language, content)['message']['result']['translatedText']
        await ctx.send(strings()['command']['translate']['strings']['template'].format(translated=translated))

    @commands.command(aliases=strings()['command']['help']['name'],
                      description=strings()['command']['help']['description'])
    async def help(self, ctx: Context, command_name: str = ''):
        if command_name:
            command = self.client.get_command(command_name)
            if not command:
                await ctx.send(strings()['command']['help']['strings']['command_not_found'].format(
                    command_name=command_name, eul_reul=eul_reul(command_name)))
                return
            params = list()
            for param_name, param in command.clean_params.items():
                if param.default:
                    params.append(f"[{param.name}: {param.annotation.__name__}]")
                else:
                    params.append(f'<{param.name}: {param.annotation.__name__}>')
            params = ' '.join(params)
            await ctx.send(strings()['command']['help']['strings']['command_template'].format(
                command=f"{get_strings()['command_prefix']}{command_name} {params}", description=command.description))
        else:
            embed = Embed(title='명령어 목록', colour=get_const()['color']['sch_vanilla'])
            for cog_name in get_strings()['cog'].keys():
                cog = self.client.get_cog(cog_name.title())
                param = list()
                for command in cog.get_commands():
                    command: Command
                    param.append(strings()['command']['help']['strings']['template'].format(
                        prefix=get_strings()['command_prefix'],
                        aliases='[' + '|'.join([command.name] + command.aliases) + ']',
                        description=command.description))
                embed.add_field(name=cog_name.title(), value='\n'.join(param), inline=False)
            await ctx.send(embed=embed)

    @commands.command(aliases=strings()['command']['analysis']['name'],
                      description=strings()['command']['analysis']['description'])
    async def analysis(self, ctx: Context, id_: int):
        time = datetime.fromtimestamp(((id_ >> 22) + 1420070400000) // 1000)
        worker = (id_ >> 17) % (1 << 5)
        process = (id_ >> 12) % (1 << 5)
        index = id_ % (1 << 12)
        embed = Embed(title=strings()['command']['analysis']['strings']['title'],
                      description=strings()['command']['analysis']['strings']['description'].format(id=id_),
                      color=get_const()['color']['sch_vanilla'])
        embed.add_field(name=strings()['command']['analysis']['strings']['time'], value=str(time), inline=False)
        embed.add_field(name=strings()['command']['analysis']['strings']['worker'], value=str(worker))
        embed.add_field(name=strings()['command']['analysis']['strings']['process'], value=str(process))
        embed.add_field(name=strings()['command']['analysis']['strings']['index'], value=str(index))
        await ctx.send(embed=embed)

    @commands.command(aliases=strings()['command']['zasokese_calendar']['name'],
                      description=strings()['command']['zasokese_calendar']['description'])
    async def zasokese_calendar(self, ctx: Context, year: int = -1, month: int = -1, day: int = -1,
                                hour: int = -1, minute: int = -1, second: int = -1):
        time = datetime.now()
        time = datetime(
            year=year if year != -1 else time.year,
            month=month if month != -1 else time.month,
            day=day if day != -1 else time.day,
            hour=hour if hour != -1 else time.hour,
            minute=minute if minute != -1 else time.minute,
            second=second if second != -1 else time.second)
        zasoque_time = ZasokDatetime.get_from_datetime(time)
        await ctx.send(strings()['command']['zasokese_calendar']['strings']['template'].format(
            year=zasoque_time.year, month=zasoque_time.month, day=zasoque_time.day))

    @commands.command(aliases=strings()['command']['lofanfashasch_id']['name'],
                      description=strings()['command']['lofanfashasch_id']['description'])
    async def lofanfashasch_id(self, ctx: Context):
        message = await ctx.send(strings()['command']['lofanfashasch_id']['strings']['notice'])
        await wait((message.add_reaction(get_strings()['emoji']['o']),
                    message.add_reaction(get_strings()['emoji']['x'])))

        def check(reaction_, user_):
            return reaction_.emoji in (get_strings()['emoji']['o'], get_strings()['emoji']['x']) and \
                   user_ == ctx.message.author

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
        except AsyncioTimeoutError:
            await message.edit(content=strings()['command']['lofanfashasch_id']['strings']['timeout'].format(
                mention=ctx.author.mention))
            return
        else:
            if reaction.emoji == get_strings()['emoji']['x']:
                await message.edit(content=strings()['command']['lofanfashasch_id']['strings']['cancelled'].format(
                    mention=ctx.author.mention))
                return

        zasoque_year = ZasokDatetime.get_from_datetime(message.created_at).year

        if ctx.guild.get_role(918751472194306048) in ctx.author.roles:
            role_number = 1
        elif ctx.guild.get_role(918756432021712997) in ctx.author.roles:
            role_number = 2
        elif ctx.guild.get_role(918756464594661406) in ctx.author.roles:
            role_number = 3
        elif ctx.guild.get_role(918756488623824926) in ctx.author.roles:
            role_number = 4
        else:
            role_number = 5

        duplication_prevent = str(ctx.author.id)[0]
        nick = f'{role_number}{zasoque_year:05d}{duplication_prevent} {ctx.author.name}'

        await ctx.author.edit(nick=nick),
        await ctx.send(strings()['command']['lofanfashasch_id']['strings']['success'].format(
            name=nick, euro=euro(nick)))


def setup(client: Bot):
    client.add_cog(Util(client))
