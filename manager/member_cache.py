from datetime import datetime, timedelta
from typing import Optional, Union

from discord import Member
from discord.ext.commands import Context, MemberConverter, MemberNotFound

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

    def optimize_cache(self):
        now = datetime.now()
        for member_id in self.members.keys():
            if self.members[member_id].last_call < now - timedelta(days=1):
                del self.members[member_id]

    def get_length(self):
        return len(self.members)

    async def get_member(self, member_id: Union[int, str], ctx: Optional[Context] = None, refresh: bool = False) \
            -> Optional[Member]:
        now = datetime.now()
        if refresh or member_id not in self.members or self.members[member_id].last_call < now - timedelta(days=1):
            # noinspection PyTypeChecker
            try:
                member = await MemberConverter().convert(ctx, member_id)
            except MemberNotFound:
                print('member is not found')
                return
            else:
                self.members[member_id] = MemberData(member, now)
        print('member is found and returned the member')
        return self.members[member_id].get_data(now)
