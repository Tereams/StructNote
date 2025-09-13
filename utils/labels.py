ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def col_label(idx: int) -> str:
    s = ""; idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = ALPHABET[r] + s
    return s
