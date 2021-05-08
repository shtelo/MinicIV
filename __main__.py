from os import listdir, environ
from threading import Thread

from discord import Intents
from discord.ext import commands

from manager import web_manager
from util import get_strings

client = commands.Bot([get_strings()['command_prefix']], intent=Intents.all(), help_command=None)

for file_name in listdir('./cogs'):
    if file_name.endswith('.py'):
        client.load_extension(f'cogs.{file_name[:-3]}')
        print(f'`{file_name}` Cog가 준비되었습니다.')

thread = Thread(target=client.run, args=(environ['MINIC_BOT_TOKEN'],))
thread.setDaemon(True)
thread.start()

web_manager.start()
