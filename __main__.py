from os import listdir, environ

from discord import Intents
from discord.ext import commands

from util import get_strings

client = commands.Bot([get_strings()['command_prefix']], intent=Intents.all(), help_command=None)

for file_name in listdir('./cogs'):
    if file_name.endswith('.py'):
        client.load_extension(f'cogs.{file_name[:-3]}')
        print(f'`{file_name}` Cog가 준비되었습니다.')

client.run(environ['MINIC_BOT_TOKEN'])
