import asyncio
import random

class PokeQueueProcessor:
    def __init__(self, queue, worker_id, db, logger=None):
        """
        Initializes the queue processor.
        :param queue: The queue from which messages are received.
        :param db: Database instance for updating processed data.
        :param logger: Logger for logging actions.
        """
        self.queue = queue
        self.db = db
        self.worker_id = worker_id
        self.logger = logger

    async def process_queue(self, max_interations=None):
        """
        Continuously processes messages from the queue.
        :param max_interations:
        :param worker_id: Unique identifier for the worker processing the queue.
        """
        iterations = 0
        while max_interations is None or iterations < max_interations:
            data = await self.queue.receive()
            if data:
                self.logger.info(f"Worker {self.worker_id} processing data: {data}")
                await asyncio.sleep(random.randint(1, 5))  # Processing
                await self.db.update_pokemon(data, 'DONE')
                self.logger.info(f"Worker {self.worker_id} completed processing for ID {data['id']}")
            else:
                self.logger.info(f"Worker {self.worker_id} queue empty, awaiting new messages.")
            await asyncio.sleep(5)  # Polling Interval
            iterations += 1
