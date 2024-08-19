import asyncio
import logging

from espeak_converter.constants import LAME_PATH
from espeak_converter.converters.espeak_converter.worker import Worker

logger = logging.getLogger(__name__)


class LameWorker(Worker):
    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue

    async def run(self):
        while item := await self.input_queue.get():
            item_id, wav_chunk = item
            if not wav_chunk:
                # Produce no-bytes output on no bytes input,
                # Because lame will produce about 200 ms of silence from empty input.
                await self.output_queue.put((item_id, b""))
                continue
            await self.output_queue.put((item_id, await self.convert_to_mp3(wav_chunk)))

    async def convert_to_mp3(self, wav_chunk):
        lame = await asyncio.create_subprocess_exec(
            LAME_PATH,
            "-r",
            "-s",
            "22050",
            "-m",
            "m",
            "-b",
            "96",
            "-",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, stderr = await lame.communicate(wav_chunk)
        if lame.returncode != 0:
            logger.error("Chunk convertion failed!")
            return self.generate_placeholder()
        return stdout

    def generate_placeholder(self):
        return b"\x00" * 40000
