import sys
from pathlib import Path

VERSION = "0.13"

if getattr(sys, "frozen", False):
    _app_file = sys.executable
else:
    _app_file = sys.modules["__main__"].__file__
APP_DIR = Path(_app_file).parent

LOG_PATH = APP_DIR / "log.log"
CONFIG_PATH = APP_DIR / "config.json"
TMP_PATH = APP_DIR / "tmp"
BOOKS_PATH = APP_DIR / "books"
LIB_PATH = APP_DIR / "lib"
UNAR_PATH = LIB_PATH / "unar.exe"
ESPEAK_DIR = LIB_PATH / "espeak"
LAME_PATH = LIB_PATH / "lame.exe"
