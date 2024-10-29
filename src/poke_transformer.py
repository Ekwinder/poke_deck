from .poke_api import PokeAPI
# from poke_db import get_next_poke_id, get_stuck_poke_id
from .poke_queue import PokeQueue


class PokeTransformer:
    def __init__(self, poke_client: PokeAPI, poke_queue: PokeQueue, db, retry, logger):
        """
        Initializes the transformer.
        :param api_client: The API client to fetch data.
        :param queue: The message queue to enqueue transformed data.
        :param db: Database instance for managing processed statuses.
        :param semaphore: Semaphore to control concurrency.
        :param logger: Logger for logging actions.
        """
        self.poke_client = poke_client
        self.poke_queue = poke_queue
        self.retry = retry
        # self.conn = conn
        self.db = db
        self.logger = logger

    async def get_pokemon_info(self) -> None:
        """
        Fetches and processes Pokemon data.
        If retry is set to True, retrieves a stuck Pokemon ID from the database.
        Otherwise, it fetches the next Pokemon ID to process.
        """
        try:
            if self.retry:
                    # get an existing poke_id
                    self.logger.info("####### Attempting to fetch stuck Pokemon ID for retry. ######")
                    poke_id = await self.db.get_stuck_poke_id()
            else:
                self.logger.info("Fetching the next Pokemon ID for processing.")

                poke_id = await self.db.get_next_poke_id()

            if not poke_id:
                self.logger.warning("No Pokemon ID found for processing.")
                return

            self.logger.info(f"Fetching data for Pokemon ID {poke_id}.")
            pokemon = await self.poke_client.get_pokemon(poke_id)
            transformed_pokemon = {'name': pokemon['name'],
                                   'id': pokemon['id'],
                                   'height': pokemon['height'] / 10,
                                   # transform the height and weight to maybe different units too
                                   'weight': pokemon['weight'] / 10, }

            await self.poke_queue.send(transformed_pokemon)
        except Exception as e:
            # TODO: push to retry queue on failure
            print("ok")
            self.logger.error(e)


