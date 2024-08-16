from pathlib import Path

from pydantic import BaseModel

from espeak_converter import constants


class ConfigModel(BaseModel):
    max_jobs: int = 2
    urls: list[str] = []
    proxy: str | None = None


class Config:
    def __init__(self, config_path):
        self.__dict__["config_path"] = Path(config_path)
        self.__dict__["_config"] = None
        self.load()

    def load(self):
        if self._config is None:
            if self.config_path.is_file():
                with self.config_path.open("r", encoding="utf-8") as f:
                    self.__dict__["_config"] = ConfigModel.model_validate_json(f.read())
            else:
                self.__dict__["_config"] = ConfigModel()

    def save(self):
        with self.config_path.open("w", encoding="utf-8") as f:
            f.write(self._config.model_dump_json(indent=2))

    def __getattr__(self, name):
        return getattr(self.__dict__["_config"], name)

    def __setattr__(self, name, value):
        return setattr(self.__dict__["_config"], name, value)


config: ConfigModel = Config(constants.CONFIG_PATH)
