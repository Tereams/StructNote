from typing import List, Optional, Tuple

class Sheet:
    def __init__(self, rows: int = 30, cols: int = 15):
        self._data: List[List[str]] = [["" for _ in range(cols)] for _ in range(rows)]
        self.current_cell: Optional[Tuple[int, int]] = None

    # 尺寸
    @property
    def rows(self) -> int: return len(self._data)
    @property
    def cols(self) -> int: return len(self._data[0]) if self._data else 0
    def shape(self) -> tuple[int, int]: return (self.rows, self.cols)

    # 读写
    def get(self, r: int, c: int) -> str: return self._data[r][c]
    def set(self, r: int, c: int, val: str) -> None: self._data[r][c] = val

    # 增删
    def add_row_end(self) -> None: self._data.append(["" for _ in range(self.cols)])
    def del_row_end(self) -> bool:
        if self.rows <= 1: return False
        self._data.pop()
        return True

    def add_col_end(self) -> None:
        for r in range(self.rows): self._data[r].append("")
    def del_col_end(self) -> bool:
        if self.cols <= 1: return False
        for r in range(self.rows): self._data[r].pop()
        return True

    # 替换全部数据（打开文件后）
    def replace_all(self, data: List[List[str]]) -> None:
        if not data or not data[0]: data = [[""]]
        self._data = [row[:] for row in data]
        self.current_cell = None

    def to_list(self) -> List[List[str]]:
        return [row[:] for row in self._data]
