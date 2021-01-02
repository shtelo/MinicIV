from util import database


class EmojiReactionManager:
    @staticmethod
    def is_reaction(emoji: str, keyword: str) -> bool:
        with database.cursor() as cursor:
            cursor.execute('SELECT * FROM emoji_reaction WHERE emoji = %s AND keyword = %s', (emoji, keyword))
            return bool(cursor.fetchall())

    @staticmethod
    def get_length() -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM emoji_reaction;')
            return cursor.fetchall()[0][0]

    def __init__(self):
        self.reactions = dict()
        self.refresh_reactions()

    def refresh_reactions(self) -> dict:
        with database.cursor() as cursor:
            cursor.execute('SELECT * FROM emoji_reaction;')
            data = cursor.fetchall()
        self.reactions = dict()
        for emoji, keyword in data:
            self.raw_add_reaction(emoji, keyword)
        return self.reactions

    def raw_add_reaction(self, emoji, keyword):
        if emoji not in self.reactions:
            self.reactions[emoji] = list()
        self.reactions[emoji].append(keyword)

    def get_reactions(self, content: str) -> set:
        reactions = set()
        for emoji, keywords in self.reactions.items():
            if emoji in reactions:
                continue
            for keyword in keywords:
                if keyword in content:
                    reactions.add(emoji)
                    break
        return reactions

    def add_reaction(self, emoji: str, keyword: str):
        with database.cursor() as cursor:
            cursor.execute('INSERT INTO emoji_reaction VALUES(%s, %s)', (emoji, keyword))
        database.commit()
        self.raw_add_reaction(emoji, keyword)

    def remove_reaction(self, emoji: str, keyword: str):
        with database.cursor() as cursor:
            cursor.execute('DELETE FROM emoji_reaction WHERE emoji = %s AND keyword = %s', (emoji, keyword))
        database.commit()
        if emoji in self.reactions and keyword in self.reactions[emoji]:
            self.reactions[emoji].remove(keyword)
            if not self.reactions[emoji]:
                del self.reactions[emoji]
