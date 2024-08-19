import asyncio
from abc import ABC, abstractmethod


class Worker(ABC):
    def __init__(self):
        self._task = None

    async def start(self):
        if self._task is not None:
            raise RuntimeError("Worker is already started")
        self._task = asyncio.create_task(self.run())

    async def wait_for_finish(self):
        if self._task is None:
            raise RuntimeError("Worker is not started")
        await self._task
        self._task = None

    @abstractmethod
    async def run(self):
        pass
