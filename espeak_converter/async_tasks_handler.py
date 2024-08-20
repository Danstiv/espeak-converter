import logging

from espeak_converter.utils.async_tasks_handler import AsyncTasksHandler

logger = logging.getLogger(__name__)

async_tasks_handler = AsyncTasksHandler()
async_tasks_handler.initialize_async_tasks_handler(logger)
