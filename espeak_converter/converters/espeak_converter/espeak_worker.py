import asyncio
import logging

from espeak_converter.constants import ESPEAK_DIR
from espeak_converter.converters.espeak_converter.worker import Worker

logger = logging.getLogger(__name__)

ESPEAK_READ_CHUNK_SIZE = 2**20  # 1MB


class EspeakWorker(Worker):
    def __init__(self, text, output_queue):
        super().__init__()
        self.text = text
        self.output_queue = output_queue
        self.is_finished = False

    async def run(self):
        self.is_finished = False
        espeak = await asyncio.create_subprocess_exec(
            ESPEAK_DIR / "espeak-ng.exe",
            f"--path={ESPEAK_DIR}",
            "--stdin",
            "-b",
            "1",
            "-v",
            "ru-cl",
            # Without sonic the highest speed is achieved without glitches.
            # https://github.com/espeak-ng/espeak-ng/issues/1461#issuecomment-1289315914
            "-s",
            "777",
            "-z",
            "--stdout",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        feed_text_task = asyncio.create_task(self._feed_text(espeak))
        await espeak.stdout.readexactly(44)  # Drop wav header
        wav_chunk = b""
        next_chunk_id = 0
        while True:
            chunk = await espeak.stdout.read(ESPEAK_READ_CHUNK_SIZE)
            if not chunk:
                # EOF
                break
            wav_chunk += chunk
            if len(wav_chunk) < ESPEAK_READ_CHUNK_SIZE:
                continue
            await self.output_queue.put((next_chunk_id, wav_chunk))
            next_chunk_id += 1
            wav_chunk = b""
        await feed_text_task
        await espeak.wait()
        if wav_chunk:
            await self.output_queue.put((next_chunk_id, wav_chunk))
            next_chunk_id += 1
        self.is_finished = True
        # Put 0 bytes chunk to avoid potential deadlock in the converter loop.
        await self.output_queue.put((next_chunk_id, b""))

    async def _feed_text(self, process):
        process.stdin.write(self.text.encode())
        await process.stdin.drain()
        process.stdin.close()
        await process.stdin.wait_closed()
