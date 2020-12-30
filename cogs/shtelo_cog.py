from asyncio import wait
from datetime import timedelta

from discord import Member, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from util import get_strings, get_const, datetime


def strings():
    return get_strings()['cog']['shtelo']


class ShteloCog(commands.Cog):
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
        reactions = []
        for i, member in enumerate(members):
            embed.add_field(name=emojis[i], value=member.mention)
            reactions.append(emojis[i])
        message = await ctx.send(embed=embed)
        await wait([message.add_reaction(reaction) for reaction in reactions])


def setup(client: Bot):
    client.add_cog(ShteloCog(client))
