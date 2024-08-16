import string
from pathlib import Path

from espeak_converter.converters.archive_converter import ArchiveConverter
from espeak_converter.converters.espeak_converter import EspeakConverter
from espeak_converter.converters.fb2_converter import FB2Converter


class PathConverter:
    def __init__(self, file_path):
        self.file_path = file_path

    @staticmethod
    def validate_path(path):
        path = str(path)
        if path.startswith('"'):
            # Path copied from Windows Explorer.
            path = path[1:-1]
        if path[0] in string.ascii_letters and path[1] == ":":
            return Path(path)

    async def run(self):
        if self.file_path.suffix == ".txt":
            converter = EspeakConverter(self.file_path)
        elif self.file_path.suffix == ".fb2":
            converter = FB2Converter(self.file_path)
        else:
            converter = ArchiveConverter(self.file_path)
        await converter.run()
