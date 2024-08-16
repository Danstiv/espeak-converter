import ssl
from urllib.parse import urlparse

import anyio
import httpx

from .base import BaseRequest, BaseRequestSender


class HTTPXRequest(BaseRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parse_result = urlparse(self.request_args[0])
        self._url = parse_result.netloc + parse_result.path
        self.request_callback = getattr(self.request_sender.client, self.method.lower())

    async def send_request(self):
        try:
            self.response = await self.request_callback(
                *self.request_args, **self.request_kwargs
            )
        except (httpx.HTTPError, anyio.EndOfStream, ssl.SSLError):
            await self.on_request_error()
            return False
        return True

    @property
    def url(self):
        return self._url

    @property
    def status_code(self):
        return self.response.status_code

    @property
    def body(self):
        return self.response.content


class HTTPXRequestSender(BaseRequestSender):
    request_class = HTTPXRequest

    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        if client is None:
            client = httpx.AsyncClient()
        self.client = client
