import re

PSEUDOTRANSLIT_TABLE = {
    "3": "з",
    "6": "б",
    "A": "А",
    "a": "а",
    "B": "В",
    "b": "в",
    "C": "С",
    "c": "с",
    "E": "Е",
    "e": "е",
    "H": "Н",
    "h": "н",
    "K": "К",
    "k": "к",
    "M": "М",
    "m": "м",
    "O": "О",
    "o": "о",
    "P": "Р",
    "p": "р",
    "T": "Т",
    "t": "т",
    "X": "Х",
    "x": "х",
    "Y": "У",
    "y": "у",
}
for k, v in list(PSEUDOTRANSLIT_TABLE.items()):
    PSEUDOTRANSLIT_TABLE.pop(k)
    PSEUDOTRANSLIT_TABLE[ord(k)] = v

RUSSIAN_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
WORD_REGEX = re.compile(
    r"(^|(?<=\s)).+?($|(?=[\s,\d-])|(?=[\.\?!](\s|$)))",
    flags=re.MULTILINE,
)


def fix_word(match):
    word = match[0]
    if len(word) == 1 and not word.isdigit():
        return PSEUDOTRANSLIT_TABLE.get(ord(word), word)
    has_russian_letters = False
    for letter in word.lower():
        if letter in RUSSIAN_ALPHABET:
            has_russian_letters = True
            break
    if not has_russian_letters:
        return word
    return word.translate(PSEUDOTRANSLIT_TABLE)


def fix_pseudotranslit(string):
    return WORD_REGEX.sub(fix_word, string)


def test():
    with open("input.txt", "rb") as f:
        text = f.read()
    text = text.decode()
    text = fix_pseudotranslit(text)
    with open("output.txt", "wb") as f:
        f.write(text.encode())
