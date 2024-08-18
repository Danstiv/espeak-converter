import asyncio
import logging

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
        lame = await asyncio.create_subprocess_exec(
            LAME_PATH,
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

        espeak_write_task = asyncio.create_task(espeak_write())

        async def lame_read():
            return await lame.stdout.read()

        lame_read_task = asyncio.create_task(lame_read())
        previous_wav_chunk = b""
        while espeak.returncode is None:
            wav_chunk = await espeak.stdout.read(65536)
            if not wav_chunk:
                continue
            if previous_wav_chunk:
                lame.stdin.write(previous_wav_chunk)
                await lame.stdin.drain()
            else:
                # Start of stream.
                header = wav_chunk[:44]
                stripped_wav_data = self.strip_zeros_from_pcm_chunk(
                    wav_chunk[44:], left=True
                )
                wav_chunk = header + stripped_wav_data
            previous_wav_chunk = wav_chunk
        previous_wav_chunk += await espeak.stdout.read()
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
