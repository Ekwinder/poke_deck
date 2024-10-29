"""
Hits Pokemon API - https://pokeapi.co/api/v2/pokemon/1 from https://pokeapi.co/docs/v2 to fetch Pokemon Data
"""
import asyncio


class PokeAPI:
    def __init__(self, base_url, client=None, logger=None):
        """
        :param base_url:
        :param client:
        :param logger:
        """
        self.base_url = base_url
        self.client = client
        self.logger = logger

    async def get_pokemon(self, poke_id: int, retry=1) -> dict:
        """
        Fetches Pokemon data from an external API.
        Includes retry logic for rate limit errors (HTTP 429).
        """
        if retry > 3:
            self.logger.error("Retry limit exceeded for ID %s", poke_id)
            raise Exception("Retry limit exceeded")

        try:
            # TODO: add check in case the URL changes, we can try to fetch the URL again from config in that case
            async with self.client.get(f"{self.base_url}/{poke_id}") as response:
                print(response.status)
                if response.status == 200:
                    self.logger.info("Successfully fetched data for ID %s", poke_id)
                    return await response.json()
                elif response.status == 404:
                    self.logger.warning("No Pokemon found for ID %s", poke_id)
                    return {}
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded, retrying for ID %s, retry - %s", poke_id, retry)
                    await asyncio.sleep(5)  # backoff
                    return await self.get_pokemon(poke_id, retry + 1)
        except Exception as e:
            if str(e) == "Retry limit exceeded":
                self.logger.error("Retry limit exceeded for ID %s", poke_id)
                raise Exception("Retry limit exceeded")
            else:
                self.logger.error("Error fetching data for ID %s: %s", poke_id, str(e))
                return {}
