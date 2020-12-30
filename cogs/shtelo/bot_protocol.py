from discord import Message


class Request:
    def __init__(self, message: Message):
        self.message = message
        tokens = message.content.split(' ', 2)
        length = len(tokens)
        self.receiver = tokens[0] if length >= 1 else None
        self.signal = tokens[1] if length >= 2 else None
        self.addition = tokens[2] if length >= 3 else None


class BotProtocol:
    ALL = 'ALL'

    ECHO = 'ECHO'
    PASS = 'PASS'
    SOMETHING = 'SOMETHING'

    def __init__(self, client):
        self.client = client

    async def on_message(self, message):
        request = Request(message)
        if message.author.id == self.client.user.id \
                or not message.author.bot \
                or request.receiver is None \
                or request.receiver not in (BotProtocol.ALL, f'<@{self.client.user.id}>', f'<@!{self.client.user.id}>'):
            return
        if request.signal == BotProtocol.ECHO:
            await self.on_echo(request)
        elif request.signal == BotProtocol.PASS:
            await self.on_pass(request)
        elif request.signal == BotProtocol.SOMETHING:
            await self.on_something(request)

    async def on_echo(self, request: Request):
        pass

    async def on_pass(self, request: Request):
        pass

    async def on_something(self, request: Request):
        pass
