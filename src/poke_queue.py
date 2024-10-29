import asyncio

class PokeQueue:
    """
    A simple queue to send and receive messages
    """
    def __init__(self,logger):
        self.queue = asyncio.Queue()
        self.logger = logger


    async def send(self, message):
        await self.queue.put(message)
        self.logger.info("Enqueued data: %s", message)

    async def receive(self):
        if not self.queue.empty():
            message = await self.queue.get()
            self.logger.info("Dequeued data: %s", message)
            return message
        return None