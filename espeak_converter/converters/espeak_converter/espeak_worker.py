import asyncio
import logging

from espeak_converter.async_tasks_handler import async_tasks_handler
from espeak_converter.config import config
from espeak_converter.constants import ESPEAK_DIR, LAME_PATH
from espeak_converter.converters.espeak_converter.constants import (
    ESPEAK_READ_CHUNK_SIZE,
)
from espeak_converter.utils.rescaler import Rescaler

logger = logging.getLogger(__name__)

default_espeak_rate_rescaler = Rescaler((0, 100), (80, 450), round_result=True)
# Based on the NVDA espeak-ng driver feature.
rate_boost_espeak_rate_rescaler = Rescaler((0, 100), (240, 1350), round_result=True)


class EspeakWorker:
    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._task = None

    async def start(self):
        if self._task is not None:
            raise RuntimeError("Worker is already started")
        self._task = async_tasks_handler.add_task(self.run())

    async def wait_for_finish(self):
        if self._task is None:
            raise RuntimeError("Worker is not started")
        await self._task
        self._task = None

    async def run(self):
        while item := await self.input_queue.get():
            id, text = item
            wav = await self.convert_text(text)
            await self.output_queue.put((id, wav))

    async def convert_text(self, text):
        rate_rescaler = (
            rate_boost_espeak_rate_rescaler
            if config.espeak.rate_boost
            else default_espeak_rate_rescaler
        )
        rate = rate_rescaler(config.espeak.rate)
        voice = (
            "ru-cl"
            if config.espeak.variant is None
            else "ru-cl+" + config.espeak.variant
        )
        espeak = await asyncio.create_subprocess_exec(
            ESPEAK_DIR / "espeak-ng.exe",
            f"--path={ESPEAK_DIR}",
            "--stdin",
            "-b",
            "1",
            "-v",
            voice,
            "-s",
            str(rate),
            "-z",
            "--stdout",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
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

        async def espeak_write():
            espeak.stdin.write(text.encode())
            await espeak.stdin.drain()
            espeak.stdin.close()
            await espeak.stdin.wait_closed()

        espeak_write_task = async_tasks_handler.add_task(espeak_write())

        async def lame_read():
            return await lame.stdout.read()

        lame_read_task = async_tasks_handler.add_task(lame_read())
        await espeak.stdout.read(44)  # Drop wav header
        previous_wav_chunk = b""
        wav_chunk = b""
        start_zeros_stripped = False
        while True:
            chunk = await espeak.stdout.read(ESPEAK_READ_CHUNK_SIZE)
            if not chunk:
                # EOF
                break
            wav_chunk += chunk
            if len(wav_chunk) < ESPEAK_READ_CHUNK_SIZE:
                continue
            if previous_wav_chunk:
                lame.stdin.write(previous_wav_chunk)
                await lame.stdin.drain()
            else:
                # Start of stream.
                wav_chunk = self.strip_zeros_from_pcm_chunk(wav_chunk, left=True)
                start_zeros_stripped = True
            previous_wav_chunk = wav_chunk
            wav_chunk = b""
        if not start_zeros_stripped:
            wav_chunk = self.strip_zeros_from_pcm_chunk(wav_chunk, left=True)
        previous_wav_chunk += wav_chunk
        if previous_wav_chunk:
            previous_wav_chunk = self.strip_zeros_from_pcm_chunk(
                previous_wav_chunk, right=True
            )
            lame.stdin.write(previous_wav_chunk)
            await lame.stdin.drain()
        lame.stdin.close()
        await lame.stdin.wait_closed()
        await espeak_write_task
        await espeak.wait()
        await lame.wait()
        stdout = await lame_read_task
        if espeak.returncode != 0 or lame.returncode != 0:
            logger.error("Chunk convertion failed!")
            return self.generate_placeholder()
        return stdout

    def generate_placeholder(self):
        return b"\x00" * 40000

    @staticmethod
    def strip_zeros_from_pcm_chunk(chunk, *, left=False, right=False):
        stripped_chunk = chunk
        if left:
            stripped_chunk = chunk.lstrip(b"\x00")
            delta = len(chunk) - len(stripped_chunk)
            if delta % 2:
                stripped_chunk = b"\x00" + stripped_chunk
        if right:
            stripped_chunk = chunk.rstrip(b"\x00")
            delta = len(chunk) - len(stripped_chunk)
            if delta % 2:
                stripped_chunk = stripped_chunk + b"\x00"
        return stripped_chunk
