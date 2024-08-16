import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod

JSONResponsePlaceholder = object()
logger = logging.getLogger(__name__)


class BaseRequestSender(ABC):
    request_class = None

    def __init__(self, max_attempts=10, request_class=None, parse_json=False):
        self.max_attempts = max_attempts
        self.request_class = request_class or self.request_class
        self.parse_json = parse_json

    async def get(self, *args, **kwargs):
        return await self("GET", *args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self("POST", *args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self("PUT", *args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self("PATCH", *args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self("DELETE", *args, **kwargs)

    async def head(self, *args, **kwargs):
        return await self("HEAD", *args, **kwargs)

    async def options(self, *args, **kwargs):
        return await self("OPTIONS", *args, **kwargs)

    async def __call__(self, method, *args, parse_json=None, **kwargs):
        if parse_json is None:
            parse_json = self.parse_json
        request = self.request_class(
            self,
            method,
            request_args=args,
            request_kwargs=kwargs,
            parse_json=parse_json,
        )
        return await request()


class BaseRequest(ABC):
    def __init__(
        self, request_sender, method, request_args, request_kwargs, parse_json=False
    ):
        self.request_sender = request_sender
        self.method = method
        self.request_args = request_args
        self.request_kwargs = request_kwargs
        self.parse_json = parse_json
        self.current_attempt = 0
        self.response = None
        self.json_response = JSONResponsePlaceholder

    async def __call__(self):
        while True:
            if not self.has_attempts:
                raise RuntimeError(f"Request to {self.url} failed")
            if self.current_attempt > 0:
                await asyncio.sleep(self.next_attempt_delay)
            self.current_attempt += 1
            success = await self.send_request()
            if not success:
                continue
            success = await self.process_response()
            if not success:
                continue
            return self.processed_response

    @abstractmethod
    async def send_request(self):
        pass

    async def on_request_error(self):
        await self.log_request_response_error(str(sys.exc_info()[1]))

    async def process_response(self):
        if self.parse_json:
            self.parse_json_response()
        if not await self.check_status_code():
            await self.on_invalid_status_code()
            return False
        if self.parse_json and self.json_response is JSONResponsePlaceholder:
            await self.on_invalid_json()
            return False
        self.processed_response = (
            self.json_response if self.parse_json else self.response
        )
        return True

    async def check_status_code(self):
        return 200 <= self.status_code < 300

    async def on_invalid_status_code(self):
        if self.status_code < 500 and self.status_code != 429:
            self.stop_retrying()
        await self.log_invalid_status_code(self.status_code)

    async def on_invalid_json(self):
        self.stop_retrying()
        await self.log_invalid_json()

    def parse_json_response(self):
        try:
            self.json_response = json.loads(self.body)
        except Exception:
            pass

    async def log_error(self, message):
        logger.error(message)

    async def log_error_with_delay(self, message):
        if self.has_attempts:
            delay = self.next_attempt_delay
            message += (
                f'\nNext attempt in {delay} {'second' if delay == 1 else 'seconds'}'
            )
        await self.log_error(message)

    async def log_request_response_error(self, message):
        await self.log_error_with_delay(f"Request to {self.url} failed: {message}")

    async def log_response_error(self, message):
        if self.json_response is not JSONResponsePlaceholder:
            response_preview = json.dumps(
                self.json_response, indent=2, ensure_ascii=False
            )
        else:
            response_preview = repr(self.body[:2048])[2:-1]  # strip b' and '
        if len(response_preview) > 2047:
            response_preview = response_preview[:2047] + "…"
        await self.log_request_response_error(
            f"{message}\n{f'Server response: {response_preview}' if response_preview else 'Server response is empty.'}"
        )

    async def log_invalid_status_code(self, status_code):
        await self.log_response_error(f"server returned code {status_code}.")

    async def log_invalid_json(self):
        await self.log_response_error("server returned invalid JSON.")

    @property
    @abstractmethod
    def url(self):
        pass

    @property
    @abstractmethod
    def status_code(self):
        pass

    @property
    @abstractmethod
    def body(self):
        pass

    @property
    def has_attempts(self):
        return self.current_attempt < self.request_sender.max_attempts

    @property
    def next_attempt_delay(self):
        return self.current_attempt**4

    def stop_retrying(self):
        self.current_attempt = self.request_sender.max_attempts
