import asyncio
import logging

import chardet

from espeak_converter.config import config
from espeak_converter.constants import BOOKS_PATH
from espeak_converter.converters.espeak_converter.espeak_worker import EspeakWorker
from espeak_converter.converters.espeak_converter.lame_worker import LameWorker

logger = logging.getLogger(__name__)


class EspeakConverter:
    def __init__(self, txt_file_path):
        self.txt_file_path = txt_file_path

    async def run(self):
        logger.info("Преобразование")
        mp3_file_path = (BOOKS_PATH / self.txt_file_path.name).with_suffix(".mp3")
        espeak_output_queue = asyncio.Queue(16)
        lame_output_queue = asyncio.Queue(16)
        text = self.read_txt_file()
        if not text:
            # Really nothing, or some decoding problem.
            return
        espeak_worker = EspeakWorker(text, espeak_output_queue)
        lame_workers = []
        # 1 job is used by espeak
        for _ in range(config.max_jobs - 1):
            lame_workers.append(LameWorker(espeak_output_queue, lame_output_queue))
        processed_chunks = {}
        next_chunk_id = 0
        mp3_file = mp3_file_path.open("wb")
        await espeak_worker.start()
        [await w.start() for w in lame_workers]
        while not espeak_worker.is_finished:
            chunk_id, chunk = await lame_output_queue.get()
            processed_chunks[chunk_id] = chunk
            while next_chunk_id in processed_chunks:
                mp3_file.write(processed_chunks.pop(next_chunk_id))
                next_chunk_id += 1
        mp3_file.close()
        await espeak_worker.wait_for_finish()
        [await espeak_output_queue.put(None) for _ in range(len(lame_workers))]
        [await w.wait_for_finish() for w in lame_workers]
        logger.info(f"Книга {mp3_file_path.name} преобразована")

    def read_txt_file(self):
        with self.txt_file_path.open("rb") as f:
            data = f.read()
        try:
            return data.decode()
        except UnicodeDecodeError:
            pass
        logger.info("Определение кодировки")
        encoding = chardet.detect(data)["encoding"]
        if not encoding:
            logger.error("Не удалось определить кодировку")
            return
        logger.info("Кодировка определена.")
        if encoding == "MacCyrillic":
            encoding = "1251"
        return data.decode(encoding)
