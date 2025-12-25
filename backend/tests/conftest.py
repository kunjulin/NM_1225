"""
Pytest 設定檔
"""
import pytest
import asyncio
from typing import Generator

# 設定 asyncio 事件迴圈
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """建立事件迴圈"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

