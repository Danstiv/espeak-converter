import asyncio
import logging

import chardet
from rich_split import TextSplitter

from espeak_converter.config import config
from espeak_converter.constants import BOOKS_PATH
from espeak_converter.converters.espeak_converter.espeak_worker import EspeakWorker

logger = logging.getLogger(__name__)


class EspeakConverter:
    def __init__(self, txt_file_path):
        self.txt_file_path = txt_file_path
        self.text_splitter = TextSplitter(1024 * 5)

    async def run(self):
        logger.info("Преобразование")
        mp3_file_path = (BOOKS_PATH / self.txt_file_path.name).with_suffix(".mp3")
        espeak_input_queue = asyncio.Queue()
        espeak_output_queue = asyncio.Queue(16)
        text = self.read_txt_file()
        if not text:
            return
        next_chunk_id = 0
        total_chunks = 0
        for i, chunk in enumerate(self.text_splitter(text), start=next_chunk_id):
            espeak_input_queue.put_nowait((i, chunk))
            total_chunks += 1
        espeak_workers = []
        # 1 worker starts up  two processes, espeak and lame.
        for _ in range(config.max_jobs // 2):
            espeak_workers.append(EspeakWorker(espeak_input_queue, espeak_output_queue))
            espeak_input_queue.put_nowait(None)
        processed_chunks_count = 0
        processed_chunks = {}
        mp3_file = mp3_file_path.open("wb")
        [await w.start() for w in espeak_workers]
        max_buffered = 0
        while processed_chunks_count < total_chunks:
            id, chunk = await espeak_output_queue.get()
            processed_chunks_count += 1
            processed_chunks[id] = chunk
            while next_chunk_id in processed_chunks:
                mp3_file.write(processed_chunks.pop(next_chunk_id))
                next_chunk_id += 1
            if len(processed_chunks) > max_buffered:
                max_buffered = len(processed_chunks)
                print(max_buffered)
        mp3_file.close()
        [await w.wait_for_finish() for w in espeak_workers]
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
