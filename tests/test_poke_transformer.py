import pytest
from unittest.mock import MagicMock, AsyncMock
import logging
from src.poke_transformer import PokeTransformer


@pytest.mark.asyncio
async def test_get_pokemon_info_success():
    """Test successful Pokemon info retrieval and transformation"""
    # Mock dependencies
    mock_api = MagicMock()
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Setup test data
    test_pokemon = {
        "id": 1,
        "name": "bulbasaur",
        "height": 70,  # Will be divided by 10
        "weight": 69,  # Will be divided by 10
    }

    expected_transformed = {
        "id": 1,
        "name": "bulbasaur",
        "height": 7.0,
        "weight": 6.9,
    }

    # Configure mocks
    mock_db.get_next_poke_id = AsyncMock(return_value=1)
    mock_api.get_pokemon = AsyncMock(return_value=test_pokemon)
    mock_queue.send = AsyncMock()

    # Create transformer instance
    transformer = PokeTransformer(
        mock_api, mock_queue, mock_db, retry=False, logger=mock_logger
    )

    # Execute
    await transformer.get_pokemon_info()

    # Verify interactions
    mock_db.get_next_poke_id.assert_called_once()
    mock_api.get_pokemon.assert_called_once_with(1)
    mock_queue.send.assert_called_once_with(expected_transformed)


@pytest.mark.asyncio
async def test_get_pokemon_info_retry():
    """Test Pokemon info retrieval in retry mode"""
    # Mock dependencies
    mock_api = MagicMock()
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Setup test data
    test_pokemon = {
        "id": 1,
        "name": "bulbasaur",
        "height": 70,
        "weight": 69,
    }

    # Configure mocks
    mock_db.get_stuck_poke_id = AsyncMock(return_value=1)
    mock_api.get_pokemon = AsyncMock(return_value=test_pokemon)
    mock_queue.send = AsyncMock()

    # Create transformer instance
    transformer = PokeTransformer(
        mock_api, mock_queue, mock_db, retry=True, logger=mock_logger
    )

    # Execute
    await transformer.get_pokemon_info()

    # Verify interactions
    mock_db.get_stuck_poke_id.assert_called_once()
    mock_api.get_pokemon.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_pokemon_info_no_id():
    """Test handling when no Pokemon ID is available"""
    # Mock dependencies
    mock_api = MagicMock()
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Configure mocks
    mock_db.get_next_poke_id = AsyncMock(return_value=0)

    # Create transformer instance
    transformer = PokeTransformer(
        mock_api, mock_queue, mock_db, retry=False, logger=mock_logger
    )

    # Execute
    await transformer.get_pokemon_info()

    # Verify interactions
    mock_db.get_next_poke_id.assert_called_once()
    mock_api.get_pokemon.assert_not_called()
    mock_queue.send.assert_not_called()


@pytest.mark.asyncio
async def test_get_pokemon_info_api_error():
    """Test handling API errors"""
    # Mock dependencies
    mock_api = MagicMock()
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Configure mocks
    mock_db.get_next_poke_id = AsyncMock(return_value=1)
    mock_api.get_pokemon = AsyncMock(side_effect=Exception("API Error"))

    # Create transformer instance
    transformer = PokeTransformer(
        mock_api, mock_queue, mock_db, retry=False, logger=mock_logger
    )

    # Execute
    await transformer.get_pokemon_info()

    # Verify interactions
    mock_db.get_next_poke_id.assert_called_once()
    mock_api.get_pokemon.assert_called_once_with(1)
    mock_queue.send.assert_not_called()