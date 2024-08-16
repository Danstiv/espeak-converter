import logging

from espeak_converter.config import config
from espeak_converter.converters.file_url_converter import URL_REGEX, FileURLConverter
from espeak_converter.converters.flibusta_url_converter import (
    FLIBUSTA_URL_REGEX,
    FlibustaURLConverter,
)
from espeak_converter.converters.path_converter import PathConverter
from espeak_converter.utils import request_utils

logger = logging.getLogger(__name__)


class Converter:
    def __init__(self):
        self.converters = []
        if config.urls:
            [self.add_url(u) for u in config.urls]
            logger.info(f"Загружено {len(config.urls)} URL")

    def add_url(self, url):
        converter = None
        if FLIBUSTA_URL_REGEX.match(url):
            converter = FlibustaURLConverter(url)
        elif URL_REGEX.match(url):
            converter = FileURLConverter(url)
        elif path := PathConverter.validate_path(url):
            converter = PathConverter(path)
        if converter is not None:
            self.converters.append((url, converter))
            return True
        else:
            logger.error("Не удалось определить тип URL")
            return False

    async def run(self):
        local_converters = []
        for url, converter in list(self.converters):
            result = await converter.run()
            if result:
                local_converters.append((url, result))
            else:
                config.urls.remove(url)
                config.save()
        for url, converters in local_converters:
            for converter in converters:
                await converter.run()
            config.urls.remove(url)
            config.save()
