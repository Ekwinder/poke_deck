"""
I used LLMs here heavily to generate test cases and coverage
"""

import pytest
import aiohttp
from unittest.mock import MagicMock, AsyncMock
import logging
from src.poke_api import PokeAPI


def create_mock_response(status, json_data=None):
    """Helper function to create a mock response"""
    mock_resp = AsyncMock()
    mock_context = AsyncMock()
    mock_context.status = status
    if json_data:
        mock_context.json = AsyncMock(return_value=json_data)
    mock_resp.__aenter__.return_value = mock_context
    return mock_resp


@pytest.mark.asyncio
async def test_get_pokemon_success():
    """Test successful Pokemon data fetch"""
    # Mock data
    mock_pokemon_data = {"id": 1, "name": "bulbasaur"}
    mock_client = MagicMock()
    mock_client.get.return_value = create_mock_response(200, mock_pokemon_data)

    # Create API instance
    api = PokeAPI(
        base_url="https://pokeapi.co/api/v2/pokemon",
        client=mock_client,
        logger=logging.getLogger()
    )

    # Test
    result = await api.get_pokemon(1)
    assert result == mock_pokemon_data
    mock_client.get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/1")


@pytest.mark.asyncio
async def test_get_pokemon_not_found():
    """Test when Pokemon is not found (404)"""
    mock_client = MagicMock()
    mock_client.get.return_value = create_mock_response(404)

    api = PokeAPI(
        base_url="https://pokeapi.co/api/v2/pokemon",
        client=mock_client,
        logger=logging.getLogger()
    )

    result = await api.get_pokemon(99999)
    assert result == {}


@pytest.mark.asyncio
async def test_get_pokemon_rate_limit():
    """Test rate limit handling with retry"""
    # First call returns 429, second call succeeds
    mock_pokemon_data = {"id": 1, "name": "bulbasaur"}
    mock_client = MagicMock()
    mock_client.get.side_effect = [
        create_mock_response(429),
        create_mock_response(200, mock_pokemon_data)
    ]

    api = PokeAPI(
        base_url="https://pokeapi.co/api/v2/pokemon",
        client=mock_client,
        logger=logging.getLogger()
    )

    result = await api.get_pokemon(1)
    assert result == mock_pokemon_data
    assert mock_client.get.call_count == 2


@pytest.mark.asyncio
async def test_get_pokemon_max_retries():
    """Test exceeding maximum retry attempts"""
    mock_client = MagicMock()
    mock_client.get.return_value = create_mock_response(429)

    api = PokeAPI(
        base_url="https://pokeapi.co/api/v2/pokemon",
        client=mock_client,
        logger=logging.getLogger()
    )

    with pytest.raises(Exception, match="Retry limit exceeded"):
        await api.get_pokemon(1)


@pytest.mark.asyncio
async def test_get_pokemon_connection_error():
    """Test handling of connection errors"""
    mock_client = MagicMock()
    mock_client.get.side_effect = aiohttp.ClientError("Connection error")

    api = PokeAPI(
        base_url="https://pokeapi.co/api/v2/pokemon",
        client=mock_client,
        logger=logging.getLogger()
    )

    result = await api.get_pokemon(1)
    assert result == {}