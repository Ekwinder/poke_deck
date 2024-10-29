import pytest
from unittest.mock import MagicMock, AsyncMock
import logging
from src.poke_queue_processor import PokeQueueProcessor


@pytest.mark.asyncio
async def test_process_queue_with_data():
    """Test processing queue with data"""
    # Mock dependencies
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Setup test data
    test_data = {"id": 1, "name": "bulbasaur", "height": 0.7, "weight": 6.9}

    # Configure mock to return data once then None
    mock_queue.receive = AsyncMock(side_effect=[test_data, None])
    mock_db.update_pokemon = AsyncMock()

    # Create processor instance
    processor = PokeQueueProcessor(mock_queue, worker_id=1, db=mock_db, logger=mock_logger)

    # Process queue (will stop after second receive returns None)
    await processor.process_queue(max_interations=1)

    # Verify interactions
    mock_queue.receive.assert_called()
    mock_db.update_pokemon.assert_called_once_with(test_data, 'DONE')


@pytest.mark.asyncio
async def test_process_queue_empty():
    """Test processing empty queue"""
    # Mock dependencies
    mock_queue = MagicMock()
    mock_db = MagicMock()
    mock_logger = logging.getLogger()

    # Configure mock to return None (empty queue)
    mock_queue.receive = AsyncMock(return_value=None)

    # Create processor instance
    processor = PokeQueueProcessor(mock_queue, worker_id=1, db=mock_db, logger=mock_logger)

    # Process queue (will stop after receive returns None)
    await processor.process_queue(max_interations=1)

    # Verify interactions
    mock_queue.receive.assert_called_once()
    mock_db.update_pokemon.assert_not_called()