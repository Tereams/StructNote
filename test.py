import tkinter as tk
from tkinter import ttk
import csv
import os
from tkinter import filedialog, messagebox


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def col_label(idx: int) -> str:
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = ALPHABET[r] + s
    return s

class MiniCSV(tk.Tk):
    def __init__(self, rows=5, cols=5):
        super().__init__()
        self.title("Mini CSV")
        self.geometry("1000x600")

        # --- 数据与尺寸 ---
        self.data = [["" for _ in range(cols)] for _ in range(rows)]
        self.cell_px_w = 100   # 单元格像素宽
        self.cell_px_h = 32    # 单元格像素高
        self.cell_char_w = 12  # Entry 的字符宽度（影响光标/文本）
        self.cell_ipady  = 2   # Entry 内边距（影响视觉高度）

        # --- 外层布局：状态栏 + 画布 + 滚动条 ---
        root = ttk.Frame(self, padding=6)
        root.pack(fill="both", expand=True)

        # 画布 & 滚动条
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.vbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        # 网格的承载 Frame（放在 Canvas 里）
        self.grid_holder = ttk.Frame(self.canvas)
        self.grid_window = self.canvas.create_window((0, 0), window=self.grid_holder, anchor="nw")

        # 摆放
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")

        # 状态栏
        self.status = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status, anchor="w").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))

        # 自适应
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # 绑定：内容变化时更新 scrollregion；画布大小变化时保持左上对齐
        self.grid_holder.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 绑定鼠标滚动（Windows/Mac/Linux）
        self._bind_mousewheel(self.canvas)

        self._build_grid()
        # --- CSV 状态 ---
        self.current_path = None  # 记录当前打开/保存的文件路径

        # --- 菜单栏 ---
        self._build_menubar()

        # --- 快捷键 ---
        self.bind_all("<Control-o>", lambda e: self.open_csv())
        self.bind_all("<Control-s>", lambda e: self.save_csv())
        self.bind_all("<Control-S>", lambda e: self.save_csv_as())


    # ---------------- 数据操作 ----------------
    def add_row_end(self):
        cols = len(self.data[0]) if self.data else 0
        self.data.append(["" for _ in range(cols)])
        self._build_grid()
        self.status.set(f"Added row -> total {len(self.data)}")

    def del_row_end(self):
        if len(self.data) <= 1:
            self.status.set("Cannot delete the last remaining row.")
            return
        self.data.pop()
        self._build_grid()
        self.status.set(f"Deleted last row -> total {len(self.data)}")

    def add_col_end(self):
        for r in range(len(self.data)):
            self.data[r].append("")
        self._build_grid()
        self.status.set(f"Added column -> total {len(self.data[0])}")

    def del_col_end(self):
        if len(self.data[0]) <= 1:
            self.status.set("Cannot delete the last remaining column.")
            return
        for r in range(len(self.data)):
            self.data[r].pop()
        self._build_grid()
        self.status.set(f"Deleted last column -> total {len(self.data[0])}")

    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Open CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            messagebox.showerror("Open CSV Failed", f"{e}")
            return

        # 归一化列数：按最长行补空串
        max_cols = max((len(r) for r in rows), default=0)
        if max_cols == 0:
            rows = [[""]]
            max_cols = 1
        norm = [r + [""] * (max_cols - len(r)) for r in rows]

        self.data = norm
        self.current_path = path
        self.status.set(f"Opened: {os.path.basename(path)}  ({len(self.data)} x {len(self.data[0])})")
        self._build_grid()

    def save_csv(self):
        # 优先保存到当前文件；如没有路径，相当于另存为
        if not self.current_path:
            return self.save_csv_as()
        self._sync_from_entries()
        try:
            with open(self.current_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(self.data)
        except Exception as e:
            messagebox.showerror("Save CSV Failed", f"{e}")
            return
        self.status.set(f"Saved: {os.path.basename(self.current_path)}")

    def save_csv_as(self):
        self._sync_from_entries()
        path = filedialog.asksaveasfilename(
            title="Save CSV As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(self.data)
        except Exception as e:
            messagebox.showerror("Save CSV Failed", f"{e}")
            return
        self.current_path = path
        self.status.set(f"Saved: {os.path.basename(path)}")

    # ---------------- 网格构建 ----------------
    def _build_grid(self):
        # 清空旧部件（只清 grid_holder 的子部件，不销毁 holder 本身）
        for w in self.grid_holder.winfo_children():
            w.destroy()

        rows = len(self.data)
        cols = len(self.data[0]) if rows else 0

        # 左上角空白
        corner = ttk.Label(self.grid_holder, text="", width=6)
        corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # 顶部列头：仅最后一列加 +/- 按钮
        for c in range(cols):
            hdr = ttk.Frame(self.grid_holder, borderwidth=1, relief="solid", padding=2)
            hdr.grid(row=0, column=c+1, sticky="nsew", padx=1, pady=1)
            ttk.Label(hdr, text=col_label(c), width=6).pack(side="left")
            if c == cols - 1:
                ttk.Button(hdr, text="+", width=3, command=self.add_col_end).pack(side="left", padx=(6,2))
                ttk.Button(hdr, text="-", width=3, command=self.del_col_end).pack(side="left", padx=2)

        # 表体
        self.entries = []
        for r in range(rows):
            # 行头：仅最后一行加 +/- 按钮
            rh = ttk.Frame(self.grid_holder, borderwidth=1, relief="solid", padding=2)
            rh.grid(row=r+1, column=0, sticky="nsew", padx=1, pady=1)
            ttk.Label(rh, text=str(r+1), width=6).pack(side="left")
            if r == rows - 1:
                ttk.Button(rh, text="+", width=3, command=self.add_row_end).pack(side="left", padx=(6,2))
                ttk.Button(rh, text="-", width=3, command=self.del_row_end).pack(side="left", padx=2)

            row_entries = []
            for c in range(cols):
                cell_frame = tk.Frame(self.grid_holder, width=self.cell_px_w, height=self.cell_px_h, bd=1, relief="solid")
                cell_frame.grid(row=r+1, column=c+1, padx=1, pady=1)
                cell_frame.grid_propagate(False)  # 固定像素大小

                e = tk.Entry(cell_frame, width=self.cell_char_w)
                e.pack(fill="both", expand=True, ipady=self.cell_ipady)
                # 载入数据
                txt = self.data[r][c]
                if txt:
                    e.insert(0, txt)
                # 写回数据
                e.bind("<FocusOut>", lambda ev, rr=r, cc=c: self._save_cell(rr, cc, ev.widget.get()))
                row_entries.append(e)
            self.entries.append(row_entries)

        # 让列/行可伸缩（可选）
        for c in range(cols + 1):
            self.grid_holder.columnconfigure(c, weight=0)
        for r in range(rows + 1):
            self.grid_holder.rowconfigure(r, weight=0)

        # 更新 scrollregion
        self.grid_holder.update_idletasks()
        self._update_scrollregion()

    def _build_menubar(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=False)
        filemenu.add_command(label="Open...    Ctrl+O", command=self.open_csv)
        filemenu.add_command(label="Save       Ctrl+S", command=self.save_csv)
        filemenu.add_command(label="Save As...", command=self.save_csv_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def _save_cell(self, r, c, val):
        if 0 <= r < len(self.data) and 0 <= c < len(self.data[0]):
            self.data[r][c] = val

    def _sync_from_entries(self):
        """把可见网格中的 entry 值写回 self.data。"""
        if not hasattr(self, "entries"):  # 初始无 entries
            return
        rows = len(self.entries)
        cols = len(self.entries[0]) if rows else 0
        # 防御：data 尺寸可能刚变化
        if rows != len(self.data) or (rows and cols != len(self.data[0])):
            return
        for r in range(rows):
            for c in range(cols):
                try:
                    self.data[r][c] = self.entries[r][c].get()
                except Exception:
                    pass


    # ---------------- 滚动支持 ----------------
    def _on_frame_configure(self, _event=None):
        # 内部内容变化时，刷新滚动区域
        self._update_scrollregion()

    def _on_canvas_configure(self, event):
        # 画布尺寸变化时，保持左上角锚定
        self.canvas.itemconfig(self.grid_window, anchor="nw")

    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, widget):
        # Windows / Mac / Linux 兼容
        widget.bind_all("<MouseWheel>", self._on_mousewheel)            # Windows / macOS(老)
        widget.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
        widget.bind_all("<Button-4>", self._on_mousewheel_linux)        # Linux 上滚
        widget.bind_all("<Button-5>", self._on_mousewheel_linux)        # Linux 下滚

    def _on_mousewheel(self, event):
        # Shift + 滚轮 已单独绑定
        if event.state & 0x0001:  # Shift 被按下
            self._on_shift_mousewheel(event)
            return
        # Windows 正负为反，macOS 可能不同；这里统一用 event.delta 的符号
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def _on_shift_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas.xview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:   # 上
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: # 下
            self.canvas.yview_scroll(1, "units")

if __name__ == "__main__":
    MiniCSV().mainloop()
