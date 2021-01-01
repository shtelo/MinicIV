from datetime import datetime, timedelta
from typing import Optional

from discord import Member
from discord.ext.commands import Context, MemberConverter

from util import singleton


class MemberData:
    def __init__(self, data: Member, last_call: datetime):
        self.__data = data
        self.last_call = last_call

    def get_data(self, now: Optional[datetime] = None) -> Member:
        if now:
            self.last_call = now
        else:
            self.last_call = datetime.now()
        return self.__data


@singleton
class MemberCache:
    def __init__(self):
        self.members = dict()

    async def get_member(self, member_id: int, ctx: Optional[Context] = None, refresh: bool = False) -> Member:
        now = datetime.now()
        if refresh or member_id not in self.members or self.members[member_id].last_call < now - timedelta(days=1):
            # noinspection PyTypeChecker
            member = await MemberConverter().convert(ctx, member_id)
            self.members[member_id] = MemberData(member, now)
        return self.members[member_id].get_data(now)
