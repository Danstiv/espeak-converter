from espeak_converter.constants import ESPEAK_DIR

ESPEAK_VOICES_DIR = ESPEAK_DIR / "espeak-ng-data/voices/!v"


def get_espeak_variants():
    variants = []
    for file in ESPEAK_VOICES_DIR.glob("*"):
        if not file.is_file():
            continue
        variants.append(file.name)
    return sorted(variants, key=lambda x: x.lower())
