"""
Have used Sqlite to store state of the data fetched from the API.
In case of multiple instances, this will handle deduplication, but in real environment we can use a DB/Cache which
can handle concurrent connections too, this is just a simple replication of that scenario
"""

import asyncio
from datetime import datetime, timedelta, UTC
from random import randint

import aiosqlite

from .config import DB_PATH


class PokeDB:
    def __init__(self, db_path=DB_PATH, conn=None, logger=None):
        """
        Initializes the database access object.
        :param db_path: Path to the SQLite database file.
        :param logger: Logger for logging actions.
        """
        self.db_path = db_path
        self.logger = logger
        self.conn = conn

    async def init_db(self):
        """
        Create the table if it does not exist
        :return:
        """
        # async with aiosqlite.connect("poke_data.db",timeout=5) as conn:
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pokemon_data (
                id INTEGER PRIMARY KEY,
                name TEXT,
                height REAL,
                weight REAL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                retry_count INTEGER DEFAULT 0,
                status TEXT CHECK(status IN ('START', 'DONE', 'FAILED')) NOT NULL DEFAULT 'START'
            )
        """)
        self.logger.info("Database initialized.")
        await self.conn.commit()

    async def get_next_poke_id(self):
        """
        get the max id from DB and insert new IDs to track data already in queue/to be pushed to queue
        :return:
        """
        try:
            # async with aiosqlite.connect("poke_data.db",timeout=10) as conn:
            cursor = await self.conn.execute("SELECT MAX(id) FROM pokemon_data")
            last_processed_id = await cursor.fetchone()
            last_processed_id = last_processed_id[0] or 0
            next_id = last_processed_id + 1
            # self.logger.info(f"Next Pokemon ID: {next_id}")

            await self.conn.execute("INSERT INTO pokemon_data (id, status) VALUES (?, 'START')", (next_id,))
            await self.conn.commit()
            return next_id
        except aiosqlite.Error as e:
            self.logger.info(e)
            await asyncio.sleep(randint(1, 10))  # Random backoff to prevent contention
            return await self.get_next_poke_id()

    async def get_stuck_poke_id(self):
        """
             Fetches the ID of a Pokemon which is stuck(STARTED for longer than specified time
             :return: The ID of the stuck Pokemon item or None if none found.

             TODO: Stuck IDs can be repeated due to the Dead letter queue being same as the main queue,
             TODO: ideally we can have a separate queue for retries with different concurrency
             """
        try:
            threshold_time = (datetime.now(UTC) - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
            # async with aiosqlite.connect("poke_data.db",timeout=10) as conn:
            cursor = await self.conn.execute(
                "SELECT id,retry_count FROM pokemon_data where status = 'START' and created < ? and retry_count < 3 ",
                (threshold_time,))
            stuck_id_tuple = await cursor.fetchone()
            stuck_id = stuck_id_tuple[0] if stuck_id_tuple else 0
            if stuck_id:
                retry_count = stuck_id_tuple[1] + 1
                await self.conn.execute("""
                           UPDATE pokemon_data
                           SET retry_count = ?
                           WHERE id = ?
                       """, (retry_count, str(stuck_id)))
                await self.conn.commit()

                await asyncio.sleep(10)
            self.logger.info(f"############## Stuck Poke ID: {stuck_id} ################")
            return stuck_id
        except aiosqlite.Error as e:
            self.logger.error(e)
            await asyncio.sleep(randint(1, 10))  # Random backoff to prevent contention

    async def update_pokemon(self, updated_pokemon: dict, status:str):
        """
       Updates the record status on receive to DONE
       :param updated_pokemon: updated information of the Pokemon
               """
        # async with aiosqlite.connect("poke_data.db",) as conn:
        try:
            await self.conn.execute("""
                UPDATE pokemon_data
                SET name = ?, height = ?, weight = ?, status = ?
                WHERE id = ?
            """, (updated_pokemon['name'], updated_pokemon['height'], updated_pokemon['weight'], status, updated_pokemon['id']))

            await self.conn.commit()
            await asyncio.sleep(randint(1, 10))  # Random backoff to prevent contention

            self.logger.info(f"Pokémon ID {updated_pokemon['id']} updated to DONE.")
        except aiosqlite.Error as e:
            self.logger.error(e)
