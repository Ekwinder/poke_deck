#!/usr/local/bin/python

import logging

import aiohttp

from src.config import BASE_API_URL, DB_PATH
from src.poke_api import PokeAPI
from src.poke_db import *
from src.poke_queue import PokeQueue
from src.poke_queue_processor import PokeQueueProcessor
from src.poke_transformer import PokeTransformer



# Define semaphores with a specific concurrency limit
max_transformers = 2  # Limit concurrent transformers to 2
max_retry_transformers = 1  # Limit concurrent transformers to 2
max_receivers = 3  # Limit concurrent receivers to 3

transformer_semaphore = asyncio.Semaphore(max_transformers)
retry_transformer_semaphore = asyncio.Semaphore(max_retry_transformers)
receiver_semaphore = asyncio.Semaphore(max_receivers)



async def poke_transform(poke_q: PokeQueue, poke_client, db, retry=False, sleep_time=3, logger=None):
    """
    :param poke_q:
    :param poke_client:
    :param db:
    :param retry:
    :param sleep_time:
    :param logger:
    :return:
    """
    if retry:
        logger.info("########## Retrying failed requests ###########")
    poke_t = PokeTransformer(poke_client, poke_q, db, retry, logger)
    while True:
        logger.info("Fetching New Pokemon data")
        await poke_t.get_pokemon_info()
        await asyncio.sleep(sleep_time)


async def transformers(poke_q: PokeQueue, poke_client, db, retry=False, logger=None):
    """
    :param poke_q:
    :param poke_client:
    :param db:
    :param retry:
    :param logger:
    :return:
    """
    async with transformer_semaphore:
        await poke_transform(poke_q, poke_client, db, retry, sleep_time=5, logger=logger)


async def retry_transformer(poke_q: PokeQueue, poke_client, db, retry=False, logger=None):
    """
    :param poke_q:
    :param poke_client:
    :param db:
    :param retry:
    :param logger:
    :return:
    """
    async with retry_transformer_semaphore:
        await poke_transform(poke_q, poke_client, db, retry, sleep_time=30, logger=logger)


async def receivers(poke_q, worker_id, db, logger):
    """
    Added queue consumer logic here along with producers
    :param poke_q:
    :param worker_id:
    :param db:
    :param logger:
    :return:
    """
    async with receiver_semaphore:
        handler = PokeQueueProcessor(poke_q, worker_id, db, logger)
        await handler.process_queue()


async def main():
    # logging.basicConfig(level=logging.INFO)
    logging.basicConfig(format="%(filename)s: %(message)s", level=logging.INFO)

    logger = logging.getLogger()

    async with aiosqlite.connect(DB_PATH) as conn:
        db = PokeDB(db_path=DB_PATH, logger=logger, conn=conn)
        await db.init_db()

        shared_queue = PokeQueue(logger)
        async with aiohttp.ClientSession() as session:
            poke_api = PokeAPI(BASE_API_URL, client=session, logger=logger)

            await asyncio.gather(
                transformers(shared_queue, poke_api, db, logger=logger),
                transformers(shared_queue, poke_api, db, logger=logger),
                retry_transformer(shared_queue, poke_api, db, retry=True, logger=logger),
                receivers(shared_queue, worker_id=1, db=db, logger=logger),
                receivers(shared_queue, worker_id=2, db=db, logger=logger),
                receivers(shared_queue, worker_id=3, db=db, logger=logger)
            )


if __name__ == '__main__':
    asyncio.run(main())
