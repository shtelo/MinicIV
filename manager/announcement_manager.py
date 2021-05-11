from typing import Optional

from discord import TextChannel
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from util import database, get_const


class AnnouncementManager:
    def __init__(self, client: Bot, channel: Optional[TextChannel] = None,
                 max_cool_message: int = get_const()['announcement-coolcount']):
        self.client = client
        self.channel = channel
        self.max_cool_message = max_cool_message

        self.cool_message = self.max_cool_message
        self.announcements = list()
        self.next_announcement_index = 0
        self.refresh_announcements()

    async def tick(self):
        self.cool_message -= 1
        if self.cool_message <= 0:
            if not self.next_announcement_index:
                self.refresh_announcements()
            self.cool_message += self.max_cool_message
            announcement = self.get_next_announcement()
            await self.channel.send(announcement['string'])

    def get_next_announcement(self) -> dict:
        if self.next_announcement_index >= len(self.announcements):
            self.next_announcement_index = 0
        announcement = self.announcements[self.next_announcement_index]
        self.next_announcement_index += 1
        return announcement

    def refresh_announcements(self):
        self.announcements = AnnouncementManager.get_announcements()
        return self

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
