import re
from datetime import datetime, timedelta

from discord.ext.commands import Converter, Context


class DatetimeConverter(Converter):
    async def convert(self, ctx: Context, argument: str) -> datetime:
        now = datetime.now()
        if re.compile(r'\d+([sS초]|[mM분]?|[hH]|시간)').fullmatch(argument):
            if argument[-1] in 'sS초':  # seconds
                duration = float(argument[:-1])
            elif argument[-1] in 'hH':
                duration = float(argument[:-1]) * 3600
            elif argument.endswith('시간'):
                duration = float(argument[:-2]) * 3600
            elif argument[-1] in 'mM분':
                duration = float(argument[:-1]) * 60
            else:
                duration = float(argument) * 60
            return now + timedelta(seconds=duration)
        elif re.compile(r'\d+:\d+(:\d+)?').fullmatch(argument):
            tokens = argument.split(':')
            hour, minute = int(tokens[0]), int(tokens[1])
            if len(tokens) == 2:
                second = 0
            else:
                second = int(tokens[2])
            return datetime(now.year, now.month, now.day, hour, minute, second)
