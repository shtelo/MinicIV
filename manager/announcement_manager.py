from time import time
from typing import Optional

from discord import TextChannel
from discord.ext import tasks
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from util import database, get_const


class AnnouncementManager:
    def __init__(self, client: Bot, channel: Optional[TextChannel] = None,
                 max_cool_time: float = 1800.0, decrease_for_message: float = 30.0):
        self.client = client
        self.channel = channel
        self.max_cool_time = max_cool_time
        self.cool_time = self.max_cool_time
        self.decrease_for_message = decrease_for_message
        self.last_call = time()
        self.announcements = []
        self.next_announcement_index = 0
        self.refresh_announcements()

    def is_cool_time_done(self) -> bool:
        if self.cool_time <= 0:
            self.cool_time += self.max_cool_time
            return True
        return False

    def tick(self):
        now = time()

        self.cool_time -= now - self.last_call

        self.last_call = now

    def get_next_announcement(self) -> dict:
        if self.next_announcement_index >= len(self.announcements):
            self.next_announcement_index = 0
        announcement = self.announcements[self.next_announcement_index]
        self.next_announcement_index += 1
        return announcement

    def refresh_announcements(self):
        self.announcements = AnnouncementManager.get_announcements()
        return self

    @tasks.loop(seconds=20.0)
    async def idler(self):
        self.tick()
        if self.channel is None:
            self.channel = self.client.get_channel(get_const()['channel']['central_park'])
        if self.is_cool_time_done():
            announcement = self.get_next_announcement()
            await self.channel.send(announcement['string'])

    @staticmethod
    def get_announcements() -> tuple:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM announcements;')
            return cursor.fetchall()

    @staticmethod
    def add_announcement(announcement: str):
        with database.cursor() as cursor:
            cursor.execute('INSERT INTO announcements(`string`) VALUES(%s)', announcement)
            database.commit()

    @staticmethod
    def delete_announcement(id_: int):
        with database.cursor() as cursor:
            cursor.execute('DELETE FROM announcements WHERE id = %s', id_)
            database.commit()

    @staticmethod
    def get_announcement(id_: int) -> dict:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM announcements WHERE id = %s', id_)
            return cursor.fetchone()
