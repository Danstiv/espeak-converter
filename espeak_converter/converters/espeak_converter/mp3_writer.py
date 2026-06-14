from pathlib import Path


class SingleFileMP3Writer:
    def __init__(self, output_path):
        self.output_path = output_path
        self.fp = None

    def open(self):
        self.fp = self.output_path.open("wb")

    def write(self, data):
        self.fp.write(data)

    def close(self):
        self.fp.close()


class DirectoryMp3Writer:
    def __init__(self, output_dir: Path, chunks_per_file: int):
        self.output_dir = output_dir
        self.chunks_per_file = chunks_per_file
        self.chunks_written = 0
        self.fp = None

    def open(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.open_next_file()

    def open_next_file(self):
        if self.fp is not None:
            self.fp.close()
        files_written = self.chunks_written // self.chunks_per_file
        next_file_name = f"{str(files_written + 1).zfill(3)}.mp3"
        file_path = self.output_dir / next_file_name
        self.fp = file_path.open("wb")

    def write(self, data):
        if self.chunks_written % self.chunks_per_file == 0:
            self.open_next_file()
        self.fp.write(data)
        self.chunks_written += 1

    def close(self):
        self.fp.close()
