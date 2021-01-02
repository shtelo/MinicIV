from asyncio import get_event_loop, sleep
from os import mkdir
from os.path import isfile, isdir
from threading import Thread
from urllib import parse

from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
from discord.ext.commands import Bot, Context
from discord.utils import get
from pytube import YouTube
from youtube_dl import YoutubeDL

from util import get_strings
from util.postposition import eul_reul


def strings():
    return get_strings()['cog']['music']


def get_video_id(value: str) -> str:
    """YouTube URL에서 영상의 id를 추출해냅니다."""

    query = parse.urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return ''


class Music(commands.Cog):
    """통화방에서 유튜브 음악을 재생하기 위해 사용되는 Cog입니다."""

    download_queue = []

    @classmethod
    def download_music(cls, url: str, filename: str):
        if not isdir('./songs'):
            mkdir('./songs')

        # noinspection SpellCheckingInspection
        cls.download_queue.append(url)
        with YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': f'./songs/{filename}.%(ext)s',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }
            ]
        }) as ydl:
            ydl.download([url])
        cls.download_queue.remove(url)

    @classmethod
    async def wait_for(cls, url: str):
        while url in cls.download_queue:
            await sleep(1)
        return

    def __init__(self, client: Bot):
        self.client = client
        self.volume = 0.02
        self.queues = {}

    def add_to_queue(self, guild_id: int, filename: str):
        self.queues[guild_id].append(filename)

    def pull_from_queue(self, guild_id: int) -> str:
        """
        반환하기 전에 queue의 맨 앞에 있는 요소를 맨 뒤로 설정하여 다음 호출 때에 다른 결과를 얻을 수 있게 합니다.

        :return: `guild_id`에 대한 대기열에서 다음으로 재생되어야 하는 순서의 노래의 filename
        """

        if self.queues:
            self.queues[guild_id] = self.queues[guild_id][1:] + self.queues[guild_id][:1]
            return self.queues[guild_id][0]
        else:
            return ''

    async def play_next(self, guild_id: int, voice, loop):
        """`guild_id`에 대한 대기열에서 다음으로 재생되어야 하는 순서의 노래를 재생하기 시작합니다."""

        if guild_id not in self.queues.keys():
            return

        if filename := self.pull_from_queue(guild_id):
            voice.play(FFmpegPCMAudio(f'songs/{filename}.mp3'),
                       after=lambda e: loop.create_task(self.play_next(guild_id, voice, loop)))
            voice.source = PCMVolumeTransformer(voice.source)
            voice.source.volume = self.volume

    async def prepare_play(self, channel, voice, guild_id):
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            await channel.connect()

        if guild_id not in self.queues.keys():
            self.queues[guild_id] = []

    async def _join(self, ctx) -> bool:
        """
        커맨드 사용자가 접속해있는 채널에 접속합니다.

        이 커맨드는 미닉이가 서버에 접속해있지 않은 경우에 self.play()를 통해서도 실행되기 때문에
        self.join()과 별도로 구별하였습니다.
        """

        if ctx.message.author.voice is None:
            await ctx.send(strings()['command']['join']['strings']['no_voice'])
            return True

        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        await self.prepare_play(channel, voice, ctx.guild.id)
        return False

    @commands.command(aliases=strings()['command']['join']['name'],
                      description=strings()['command']['join']['description'])
    async def join(self, ctx: Context):
        """커맨드 사용자가 접속해있는 채널에 접속합니다."""

        if not await self._join(ctx):
            channel = ctx.message.author.voice.channel
            await ctx.send(strings()['command']['join']['strings']['connected'].format(channel=str(channel.mention)))

    @commands.command(aliases=strings()['command']['leave']['name'],
                      description=strings()['command']['leave']['description'])
    async def leave(self, ctx):
        """커맨드가 사용된 서버에 접속해있는 음성채팅채널에서 퇴장합니다."""

        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            del self.queues[ctx.guild.id]
            await voice.disconnect()
            await ctx.send(strings()['command']['leave']['strings']['left'].format(channel=str(channel)))

    @commands.command(aliases=strings()['command']['play']['name'],
                      description=strings()['command']['play']['description'])
    async def play(self, ctx, url: str):
        """커맨드가 사용된 서버에 연결되어있는 채널에서 입력받은 YouTube URL의 영상의 오디오를 재생합니다."""

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if not voice or not voice.is_connected():
            if await self._join(ctx):
                return
            voice = get(self.client.voice_clients, guild=ctx.guild)

        video_id = get_video_id(url)

        message = None

        if not isfile(f'songs/{video_id}.mp3'):
            message = await ctx.send(strings()['command']['play']['strings']['downloading']
                                     .format(url=url, eul_reul=eul_reul(url)))
            thread = Thread(target=Music.download_music, args=(url, video_id))
            thread.setDaemon(False)
            thread.start()

        await Music.wait_for(url)

        self.add_to_queue(ctx.guild.id, video_id)
        if not (voice and voice.is_playing()):
            await self.play_next(ctx.guild.id, voice, get_event_loop())
            if message:
                await message.edit(content=strings()['command']['play']['strings']['playing']
                                   .format(url=url, eul_reul=eul_reul(url)))
            else:
                await ctx.send(strings()['command']['play']['strings']['playing']
                               .format(url=url, eul_reul=eul_reul(url)))
        else:
            if message:
                await message.edit(content=strings()['command']['play']['strings']['queued']
                                   .format(url=url, eul_reul=eul_reul(url)))
            else:
                await ctx.send(strings()['command']['play']['strings']['queued']
                               .format(url=url, eul_reul=eul_reul(url)))

    @commands.command(aliases=strings()['command']['dequeue']['name'],
                      description=strings()['command']['dequeue']['description'])
    async def dequeue(self, ctx, video_id: str = str()):
        """`video_id`를 대기열에서 제외합니다."""

        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            if not video_id:
                video_id = self.queues[ctx.guild.id][0]

            try:
                self.queues[ctx.guild.id].remove(video_id)
            except ValueError:
                await ctx.send(strings()['command']['dequeue']['strings']['not_in_queue']
                               .format(filename=video_id, eul_reul=eul_reul(video_id)))
            else:
                await ctx.send(strings()['command']['dequeue']['strings']['deleted'].format(filename=video_id))

    @commands.command(aliases=strings()['command']['show_queue']['name'],
                      description=strings()['command']['show_queue']['description'])
    async def show_queue(self, ctx):
        if ctx.guild.id in self.queues.keys():
            message = await ctx.send(strings()['command']['show_queue']['strings']['loading'])
            count = len(self.queues[ctx.guild.id])
            result = f"{strings()['command']['show_queue']['strings']['there_are'].format(count=count)}"
            for i in range(count):
                filename = self.queues[ctx.guild.id][i]
                line = f"\n> `{i}.` {YouTube(f'https://youtu.be/{filename}').title}(`{filename}`)"
                if len(result) + len(line) > 2000:
                    break
                result += line
            await message.edit(content=result)
        else:
            await ctx.send(strings()['command']['show_queue']['strings']['no_queue'])

    @commands.command(aliases=strings()['command']['skip']['name'],
                      description=strings()['command']['skip']['description'])
    async def skip(self, ctx):
        """커맨드가 사용된 서버에서 재생중인 음악을 건너뛰고 대기열의 다음 음악을 재생합니다."""

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.stop()
            await ctx.send(strings()['command']['skip']['strings']['skipped'])
        else:
            await ctx.send(strings()['command']['skip']['strings']['not_playing'])

    @commands.command(aliases=strings()['command']['pause']['name'],
                      description=strings()['command']['pause']['description'])
    async def pause(self, ctx):
        """커맨드가 사용된 서버에서 재생중인 음악을 일시정지합니다."""

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.pause()
            await ctx.send(strings()['command']['pause']['strings']['paused'])
        else:
            await ctx.send(strings()['command']['pause']['strings']['not_playing'])

    @commands.command(aliases=strings()['command']['resume']['name'],
                      description=strings()['command']['resume']['description'])
    async def resume(self, ctx):
        """커맨드가 사용된 서버에서 일시정지된 음악을 재개합니다."""

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            voice.resume()
            await ctx.send(strings()['command']['resume']['strings']['resumed'])
        else:
            await ctx.send(strings()['command']['resume']['strings']['not_paused'])

    @commands.command(aliases=strings()['command']['volume']['name'],
                      description=strings()['command']['volume']['description'])
    async def volume(self, ctx, volume: float = None):
        """커맨드가 사용된 서버에서 사용할 볼륨을 설정합니다."""

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if volume is None:
            await ctx.send(strings()['command']['volume']['strings']['now'].format(volume=int(self.volume * 100)))
        else:
            if voice and voice.is_playing():
                self.volume = volume / 100
                voice.source.volume = self.volume
                await ctx.send(strings()['command']['volume']['strings']['set'].format(volume=volume))
            else:
                await ctx.send(strings()['command']['volume']['strings']['not_playing'])


def setup(client):
    client.add_cog(Music(client))
