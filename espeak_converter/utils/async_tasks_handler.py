import asyncio
import logging
import signal

default_logger = logging.getLogger('async_tasks_handler_default_logger')


class AsyncTasksHandler:

    def initialize_async_tasks_handler(self, logger=None):
        self._logger = logger or default_logger
        self._async_tasks = set()
        self._previous_signal_handlers = {}
        self._stop_signal_received_event = asyncio.Event()
        self._all_tasks_finished_event = asyncio.Event()
        self._all_tasks_finished_event.set()

    def add_task(self, coro, name=None, cancellable=True):
        name = name or coro.__name__
        task = asyncio.create_task(coro, name=name)
        task.add_done_callback(self.task_done_callback)
        task.cancellable = cancellable
        self._async_tasks.add(task)
        self._logger.debug(f'Added task "{name}"')
        self._all_tasks_finished_event.clear()
        return task

    def task_done_callback(self, task):
        task_name = task.get_name()
        if task.cancelled():
            self._logger.debug(f'Task "{task_name}" cancelled')
        elif exception := task.exception():
            self._logger.exception(f'Unhandeled exception in task "{task_name}":', exc_info=exception)
        else:
            self._logger.debug(f'Task "{task_name}" finished')
        self._async_tasks.remove(task)
        if not self._async_tasks:
            self._all_tasks_finished_event.set()

    async def stop_tasks(self):
        self._logger.debug('Stopping tasks')
        for task in self._async_tasks:
            task_name = task.get_name()
            if not task.cancellable:
                self._logger.debug(f'Skipping task "{task_name}" because it is marked as uncancellable')
                continue
            self._logger.debug(f'Cancelling task "{task_name}"')
            task.cancel()
        self._logger.debug('Waiting for tasks to complete')
        await self.wait_for_tasks_completion()

    async def wait_for_tasks_completion(self):
        await self._all_tasks_finished_event.wait()

    def set_stop_signal_handler(self, stop_signal=signal.SIGINT):
        if self._previous_signal_handlers.get(stop_signal) is not None:
            raise ValueError('Stop signal handler is already set for that signal')
        try:
            asyncio.get_running_loop().add_signal_handler(stop_signal, self._stop_signal_handler)
            self._previous_signal_handlers[stop_signal] = True
        except NotImplementedError:
            self._previous_signal_handlers[stop_signal] = signal.signal(stop_signal, self._stop_signal_handler)

    def unset_stop_signal_handler(self, stop_signal=signal.SIGINT):
        if self._previous_signal_handlers.get(stop_signal) is None:
            raise ValueError('Stop signal handler is already unset for that signal')
        if self._previous_signal_handlers[stop_signal] == True:
            asyncio.get_running_loop().remove_signal_handler(stop_signal)
        else:
            signal.signal(stop_signal, self._previous_signal_handlers[stop_signal])
        del self.previous_signal_handlers[stop_signal]

    def _stop_signal_handler(self, *args, **kwargs):
        self._stop_signal_received_event.set()

    async def wait_for_stop_signal(self):
        if not self._previous_signal_handlers:
            raise ValueError('Stop signal handler is not set')
        await self._stop_signal_received_event.wait()
        self._stop_signal_received_event.clear()
