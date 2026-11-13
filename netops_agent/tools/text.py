import re

def ascii_clean(s: str) -> str:
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)   # all dash/hyphen variants
    return s.replace("\u2018", "'").replace("\u2019", "'")