import pytest
import logging
from src.poke_queue import PokeQueue


@pytest.mark.asyncio
async def test_send_message():
    """Test sending a message to the queue"""
    queue = PokeQueue(logging.getLogger())
    test_message = {"id": 1, "name": "bulbasaur"}

    await queue.send(test_message)
    assert queue.queue.qsize() == 1


@pytest.mark.asyncio
async def test_receive_message():
    """Test receiving a message from the queue"""
    queue = PokeQueue(logging.getLogger())
    test_message = {"id": 1, "name": "bulbasaur"}

    await queue.send(test_message)
    received_message = await queue.receive()

    assert received_message == test_message
    assert queue.queue.empty()


@pytest.mark.asyncio
async def test_receive_empty_queue():
    """Test receiving from an empty queue"""
    queue = PokeQueue(logging.getLogger())

    received_message = await queue.receive()
    assert received_message is None