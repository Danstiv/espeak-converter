import asyncio
import logging
import shutil

from custom_logging_formatter import Formatter
from espeak_converter import constants
from espeak_converter.config import config
from espeak_converter.converter import Converter
from espeak_converter.ui import UI
from espeak_converter.utils import request_utils

logger = logging.getLogger("espeak_converter")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(console_handler)
file_handler = logging.FileHandler(constants.LOG_PATH)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    Formatter(
        "%(asctime)s - %(levelname)s - %(module)s.%(funcName)s (%(lineno)d)\n%(message)s"
    )
)
logger.addHandler(file_handler)


async def main():
    logger.info(f"eSpeak converter v{constants.VERSION}")
    constants.TMP_PATH.mkdir(exist_ok=True)
    constants.BOOKS_PATH.mkdir(exist_ok=True)
    request_utils.set_proxy(config.proxy)
    converter = Converter()
    ui = UI(converter)
    result = await ui.start()
    shutil.rmtree(constants.TMP_PATH, ignore_errors=True)
    return result


if __name__ == "__main__":
    result = None
    try:
        result = asyncio.run(main())
    except Exception:
        logger.exception("Необработанное исключение:")
    if result is None:
        input("Нажмите Enter для выхода.")
