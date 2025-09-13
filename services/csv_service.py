import csv
from typing import List

def load_csv(path: str) -> List[List[str]]:
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    max_cols = max((len(r) for r in rows), default=0)
    if max_cols == 0:
        return [[""]]
    return [r + [""] * (max_cols - len(r)) for r in rows]

def save_csv(path: str, data: List[List[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(data)
