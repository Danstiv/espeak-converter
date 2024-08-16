from fb2parser import FB2Parser

from espeak_converter.constants import TMP_PATH
from espeak_converter.converters.espeak_converter import EspeakConverter


class FB2Converter:
    def __init__(self, fb2_file_path):
        self.fb2_file_path = fb2_file_path

    async def run(self):
        txt_file_path = (TMP_PATH / self.fb2_file_path.name).with_suffix(".txt")
        with self.fb2_file_path.open("rb") as f:
            content = f.read()
        content = FB2Parser(content, lang="ru").parse()
        with txt_file_path.open("wb") as f:
            f.write(content.encode())
        converter = EspeakConverter(txt_file_path)
        await converter.run()
        txt_file_path.unlink()
