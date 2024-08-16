import logging
import os
import re
from email.message import EmailMessage

from espeak_converter.constants import TMP_PATH
from espeak_converter.converters.path_converter import PathConverter
from espeak_converter.utils.request_utils import http_client

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://.+?\..+")


class FileURLConverter:
    def __init__(self, file_url):
        self.file_url = file_url

    async def run(self):
        logger.info(f"Скачивание {self.file_url}")
        response = await http_client.get(self.file_url)
        filename = None
        if "Content-Disposition" in response.headers:
            message = EmailMessage()
            message["Content-Disposition"] = response.headers["Content-Disposition"]
            filename = message["Content-Disposition"].params["filename"]
        if not filename:
            filename = os.path.split(self.file_url)[-1]
        if "/" in filename or ".." in filename or len(filename.encode()) > 255:
            logger.error("Некорректное имя файла")
            return
        file_path = TMP_PATH / filename
        with file_path.open("wb") as f:
            f.write(response.content)
        converter = PathConverter(file_path)
        return [converter]
