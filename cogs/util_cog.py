from asyncio import wait, TimeoutError as AsyncioTimeoutError

from discord import VoiceChannel, Message
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandNotFound, CommandError, TextChannelConverter
from pymysql.cursors import DictCursor

from cogs.shtelo.bot_protocol import BotProtocol, Request
from manager import Memo
from util import eul_reul, euro, i_ga, database, load_strings, get_strings, eun_neun, a_ya


def strings():
    return get_strings()['cog']['util']


class MemoManager:
    @staticmethod
    def get(key: str) -> Memo:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT * FROM memos WHERE `key` = %s;', key)
            result = cursor.fetchall()[0]
            return Memo(result['value'], result['author_id'])

    @staticmethod
    def get_value(key: str) -> str:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT value FROM memos WHERE `key` = %s;', key)
            data = cursor.fetchall()
            return data[0]['value']

    @staticmethod
    def get_keys() -> tuple:
        cursor = database.cursor()
        cursor.execute('SELECT `key` FROM memos;')
        return tuple([column[0] for column in cursor.fetchall()])

    @staticmethod
    def get_author_id(key: str) -> int:
        with database.cursor(DictCursor) as cursor:
            cursor.execute(f'SELECT author_id FROM memos WHERE `key` = %s;', key)
            data = cursor.fetchall()
            return data[0]['author_id']

    @staticmethod
    def insert(key: str, memo: Memo):
        cursor = database.cursor()
        cursor.execute('INSERT INTO memos VALUES(%s, %s, %s);', (key, memo.content, memo.author_id))
        database.commit()

    @staticmethod
    def update(key: str, memo: Memo):
        cursor = database.cursor()
        cursor.execute('UPDATE memos SET value = %s WHERE `key` = %s;', (memo.content, key))
        database.commit()

    @staticmethod
    def delete(key: str):
        cursor = database.cursor()
        cursor.execute('DELETE FROM memos WHERE `key` = %s;', key)
        database.commit()

    @staticmethod
    def is_key(key: str) -> bool:
        cursor = database.cursor()
        return cursor.execute('SELECT * FROM memos WHERE `key` = %s;', key)


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

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        await self.bot_protocol.on_message(message)

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
        tasks = []
        print(from_channel.members)
        for member in from_channel.members:
            tasks.append(member.edit(voice_channel=to_channel))  # todo this has error
        await wait(tasks)

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

        tasks = []
        for voice_channel in ctx.guild.voice_channels:
            if voice_channel.id not in (ctx.guild.afk_channel.id, destination_channel.id):
                for member in voice_channel.members:
                    tasks.append(member.edit(voice_channel=destination_channel))

        await wait(tasks)

    @commands.group(aliases=strings()['command']['memo']['name'],
                    description=strings()['command']['memo']['description'],
                    invoke_without_command=True)
    async def memo(self, ctx: Context, key: str):
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


def setup(client: Bot):
    client.add_cog(Util(client))