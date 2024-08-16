import asyncio
import logging
import os

from espeak_converter.constants import ESPEAK_DIR, LAME_PATH

logger = logging.getLogger(__name__)


class EspeakWorker:
    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._task = None

    async def start(self):
        if self._task is not None:
            raise RuntimeError("Worker is already started")
        self._task = asyncio.create_task(self.run())

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
        read_end, write_end = os.pipe()
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
            "--stdout",
            stdin=asyncio.subprocess.PIPE,
            stdout=write_end,
            stderr=asyncio.subprocess.DEVNULL,
        )
        lame = await asyncio.create_subprocess_exec(
            LAME_PATH,
            "-b",
            "96",
            "-",
            "-",
            stdin=read_end,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        espeak_task = asyncio.create_task(espeak.communicate(text.encode()))
        lame_task = asyncio.create_task(lame.communicate())
        await espeak_task
        with open(write_end, "ab") as f:
            f.flush()
        stdout, stderr = await lame_task
        if espeak.returncode != 0 or lame.returncode != 0:
            logger.error("Chunk convertion failed!")
            return self.generate_placeholder()
        return stdout

    def generate_placeholder(self):
        return b"\x00" * 40000
