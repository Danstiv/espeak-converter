import httpx

from espeak_converter.utils.constants import REQUEST_HEADERS
from espeak_converter.utils.request_sender.httpx import HTTPXRequest, HTTPXRequestSender


class CustomRequest(HTTPXRequest):
    async def log_request_response_error(self, message):
        await self.log_error_with_delay(f"Запрос не удался: {message}")

    @property
    def next_attempt_delay(self):
        return min(self.current_attempt**2, 30)


class RequestSender(HTTPXRequestSender):
    request_class = CustomRequest


def _create_httpx_client(**kwargs):
    client = httpx.AsyncClient(timeout=120, follow_redirects=True, **kwargs)
    client.headers = REQUEST_HEADERS
    return client


http_client = RequestSender(max_attempts=float("inf"), client=_create_httpx_client())


def set_proxy(proxy):
    if proxy is None:
        proxies = {}
    else:
        proxies = {"http://": proxy, "https://": proxy}
    http_client.client = _create_httpx_client(proxies=proxies)
