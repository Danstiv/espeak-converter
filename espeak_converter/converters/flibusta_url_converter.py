import logging
import re

from espeak_converter.converters.file_url_converter import FileURLConverter
from espeak_converter.utils.request_utils import http_client

logger = logging.getLogger(__name__)

FB2_BOOK_URL_REGEX = re.compile(r'href="(/b/\d+/fb2)"')
FLIBUSTA_URL_REGEX = re.compile(r"^https?://flibusta\.is.*?(?<!/fb2)$")
FLIBUSTA_URL = "https://flibusta.is"


class FlibustaURLConverter:
    def __init__(self, flibusta_url):
        self.flibusta_url = flibusta_url

    async def run(self):
        logger.info("Парсинг страницы флибусты")
        response = await http_client.get(self.flibusta_url)
        urls = FB2_BOOK_URL_REGEX.findall(response.content.decode())
        urls = [FLIBUSTA_URL + u for u in urls]
        logger.info(f"Найдено {len(urls)} книг")
        url_converters = [FileURLConverter(url) for url in urls]
        local_converters = []
        for converter in url_converters:
            local_converters.extend(await converter.run())
        return local_converters
