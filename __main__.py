from os import listdir, environ
from threading import Thread

from discord import Intents
from discord.ext import commands

from rest import Launcher
from util import get_strings

client = commands.Bot([get_strings()['command_prefix']], intent=Intents.all(), help_command=None)
restful_launcher = Launcher()

for file_name in listdir('./rest'):
    if file_name.endswith('.py') \
            and '__init__' not in file_name \
            and 'launcher' not in file_name:
        restful_launcher.load_resource(f'rest.{file_name[:-3]}')
        print(f'`{file_name}` Resource가 준비되었습니다.')

for file_name in listdir('./cogs'):
    if file_name.endswith('.py'):
        client.load_extension(f'cogs.{file_name[:-3]}')
        print(f'`{file_name}` Cog가 준비되었습니다.')

client_thread = Thread(target=client.run, args=(environ['MINIC_BOT_TOKEN'],))
client_thread.setDaemon(True)
client_thread.start()
restful_launcher.run(host='0.0.0.0', port=3375)
