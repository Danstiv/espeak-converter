import asyncio
import logging
import shutil

from espeak_converter.constants import TMP_PATH, UNAR_PATH
from espeak_converter.converters.espeak_converter import EspeakConverter
from espeak_converter.converters.fb2_converter import FB2Converter

logger = logging.getLogger(__name__)


class ArchiveConverter:
    def __init__(self, archive_file_path):
        self.archive_file_path = archive_file_path
        self.archive_output_path = (
            TMP_PATH / ("archive-" + self.archive_file_path.name)
        ).with_suffix("")

    async def run(self):
        logger.info("Распаковка архива")
        logger.debug(f"Archive path: {self.archive_file_path}")
        self.archive_output_path.mkdir()
        process = await asyncio.create_subprocess_exec(
            UNAR_PATH,
            "-o",
            self.archive_output_path,
            self.archive_file_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        if process.returncode != 0:
            logger.error("Не удалось распаковать архив")
            await self.cleanup()
            return
        converters = []
        for file in self.archive_output_path.rglob("*.*"):
            if file.suffix == ".txt":
                converters.append(EspeakConverter(file))
            if file.suffix == ".fb2":
                converters.append(FB2Converter(file))
        if not converters:
            logger.info("Текстовые файлы в архиве не обнаружены")
            await self.cleanup()
            return
        [await c.run() for c in converters]
        await self.cleanup()

    async def cleanup(self):
        shutil.rmtree(self.archive_output_path)
