import os
import csv
import tkinter as tk
from tkinter import ttk
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
    def __init__(self, rows=30, cols=15):
        super().__init__()
        self.title("Mini CSV - Untitled")
        self.geometry("1200x700")

        # --- 数据与尺寸 ---
        self.data = [["" for _ in range(cols)] for _ in range(rows)]
        # 单元格像素与Entry字符宽（像素控制展示尺寸，字符宽仅影响光标与输入体验）
        self.cell_px_w = 120
        self.cell_px_h = 34
        self.cell_char_w = 14
        self.cell_ipady  = 2

        # 省略号显示（左侧“展示模式”）——字符数近似
        self.display_char_limit = 20

        # CSV 状态
        self.current_path = None

        # 当前选中单元格与编辑焦点标记
        self.current_cell = None       # (r, c) or None
        self._in_cell_focus = False

        # --- 外层左右分栏 ---
        self.pane = tk.PanedWindow(self, orient="horizontal")
        self.pane.pack(fill="both", expand=True)

        # 左侧区域（表格 + 滚动条 + 状态栏）
        left = ttk.Frame(self.pane)
        self.pane.add(left, stretch="always")

        # 右侧区域（多行文本编辑器）
        right = ttk.Frame(self.pane, padding=6)
        self.pane.add(right, width=420)

        # --- 左侧内部布局 ---
        root = ttk.Frame(left, padding=6)
        root.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.vbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        self.grid_holder = ttk.Frame(self.canvas)
        self.grid_window = self.canvas.create_window((0, 0), window=self.grid_holder, anchor="nw")

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status, anchor="w").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # --- 右侧多行编辑器 ---
        ttk.Label(right, text="Cell Editor (multi-line):", anchor="w").pack(fill="x", pady=(0, 4))
        self.editor = tk.Text(right, wrap="word", height=10, undo=True)
        self.editor.pack(fill="both", expand=True)

        btnbar = ttk.Frame(right)
        btnbar.pack(fill="x", pady=(6, 0))
        ttk.Button(btnbar, text="Apply ▶", command=self._apply_from_editor).pack(side="left")
        ttk.Button(btnbar, text="Clear", command=lambda: self.editor.delete("1.0", "end")).pack(side="left", padx=6)

        # 编辑器输入时即时同步
        self.editor.bind("<KeyRelease>", self._editor_on_change)

        # 绑定：内容变化时更新 scrollregion；画布大小变化时保持左上对齐
        self.grid_holder.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 绑定鼠标滚轮（Windows/Mac/Linux）
        self._bind_mousewheel(self.canvas)

        # 菜单栏 + 快捷键
        self._build_menubar()
        self.bind_all("<Control-o>", lambda e: self.open_csv())
        self.bind_all("<Control-s>", lambda e: self.save_csv())
        self.bind_all("<Control-S>", lambda e: self.save_csv_as())

        # 初次构建网格
        self._build_grid()

    # ======================= 网格构建与单元格 =======================
    def _build_grid(self):
        # 清空旧部件
        for w in self.grid_holder.winfo_children():
            w.destroy()

        rows = len(self.data)
        cols = len(self.data[0]) if rows else 0

        # 左上角空白
        corner = ttk.Label(self.grid_holder, text="", width=6)
        corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # 顶部列头：仅最后一列带 +/- 按钮
        for c in range(cols):
            hdr = ttk.Frame(self.grid_holder, borderwidth=1, relief="solid", padding=2)
            hdr.grid(row=0, column=c + 1, sticky="nsew", padx=1, pady=1)
            ttk.Label(hdr, text=col_label(c), width=6).pack(side="left")
            if c == cols - 1:
                ttk.Button(hdr, text="+", width=3, command=self.add_col_end).pack(side="left", padx=(6, 2))
                ttk.Button(hdr, text="-", width=3, command=self.del_col_end).pack(side="left", padx=2)

        # 表体
        self.entries = []
        for r in range(rows):
            # 行头：仅最后一行带 +/- 按钮
            rh = ttk.Frame(self.grid_holder, borderwidth=1, relief="solid", padding=2)
            rh.grid(row=r + 1, column=0, sticky="nsew", padx=1, pady=1)
            ttk.Label(rh, text=str(r + 1), width=6).pack(side="left")
            if r == rows - 1:
                ttk.Button(rh, text="+", width=3, command=self.add_row_end).pack(side="left", padx=(6, 2))
                ttk.Button(rh, text="-", width=3, command=self.del_row_end).pack(side="left", padx=2)

            row_entries = []
            for c in range(cols):
                cell_frame = tk.Frame(
                    self.grid_holder, width=self.cell_px_w, height=self.cell_px_h, bd=1, relief="solid"
                )
                cell_frame.grid(row=r + 1, column=c + 1, padx=1, pady=1)
                cell_frame.grid_propagate(False)  # 固定像素大小

                e = tk.Entry(cell_frame, width=self.cell_char_w)
                e.pack(fill="both", expand=True, ipady=self.cell_ipady)

                full_txt = self.data[r][c]
                # 默认“展示模式”（省略号）
                self._entry_set_display_mode(e, full_txt, editing=False)

                def on_focus_in(ev, rr=r, cc=c, ent=e):
                    self.current_cell = (rr, cc)
                    self._in_cell_focus = True
                    # 焦点进入 -> 显示完整文本
                    self._entry_set_display_mode(ent, self.data[rr][cc], editing=True)
                    # 右侧编辑器加载
                    self._load_editor_from_cell(rr, cc)

                def on_focus_out(ev, rr=r, cc=c, ent=e):
                    self._in_cell_focus = False
                    # 保存到数据
                    self._save_cell(rr, cc, ent.get())
                    # 切回“展示模式”
                    self._entry_set_display_mode(ent, self.data[rr][cc], editing=False)
                    # 若仍选中该格，刷新右侧
                    if self.current_cell == (rr, cc):
                        self._load_editor_from_cell(rr, cc)

                e.bind("<FocusIn>", on_focus_in)
                e.bind("<FocusOut>", on_focus_out)

                row_entries.append(e)
            self.entries.append(row_entries)

        # 列/行权重
        for c in range(cols + 1):
            self.grid_holder.columnconfigure(c, weight=0)
        for r in range(rows + 1):
            self.grid_holder.rowconfigure(r, weight=0)

        # 更新滚动区域与标题
        self.grid_holder.update_idletasks()
        self._update_scrollregion()
        name = os.path.basename(self.current_path) if self.current_path else "Untitled"
        self.title(f"Mini CSV - {name}  ({len(self.data)} x {len(self.data[0])})")

        # 可选：恢复焦点
        if self.current_cell:
            rr, cc = self.current_cell
            if 0 <= rr < len(self.data) and 0 <= cc < len(self.data[0]):
                try:
                    self.entries[rr][cc].focus_set()
                except Exception:
                    pass

    # ======================= 数据操作（增删行列） =======================
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
        # 校正 current_cell
        if self.current_cell and self.current_cell[0] >= len(self.data):
            self.current_cell = (len(self.data) - 1, self.current_cell[1])
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
        # 校正 current_cell
        if self.current_cell and self.current_cell[1] >= len(self.data[0]):
            self.current_cell = (self.current_cell[0], len(self.data[0]) - 1)
        self._build_grid()
        self.status.set(f"Deleted last column -> total {len(self.data[0])}")

    # ======================= 右侧编辑器同步 =======================
    def _load_editor_from_cell(self, r: int, c: int):
        """把 data[r][c] 的完整文本装载到右侧编辑器。"""
        self.editor.unbind("<KeyRelease>")  # 防止设置文本时触发回写
        try:
            self.editor.delete("1.0", "end")
            if 0 <= r < len(self.data) and 0 <= c < len(self.data[0]):
                self.editor.insert("1.0", self.data[r][c] or "")
        finally:
            self.editor.bind("<KeyRelease>", self._editor_on_change)

    def _apply_from_editor(self):
        """按钮 Apply：将右侧文本写回当前单元格。"""
        if not self.current_cell:
            self.status.set("No cell selected.")
            return
        r, c = self.current_cell
        new_txt = self.editor.get("1.0", "end-1c")
        self._save_cell(r, c, new_txt)
        # 刷新左侧对应 Entry 的显示
        try:
            ent = self.entries[r][c]
        except Exception:
            ent = None
        if ent:
            self._entry_set_display_mode(
                ent, new_txt, editing=(self._in_cell_focus and self.current_cell == (r, c))
            )
        self.status.set(f"Updated cell ({r+1}, {c+1}) from editor.")

    def _editor_on_change(self, _event=None):
        """键入即时同步（无需点 Apply）。"""
        if not self.current_cell:
            return
        r, c = self.current_cell
        new_txt = self.editor.get("1.0", "end-1c")
        self._save_cell(r, c, new_txt)
        try:
            ent = self.entries[r][c]
        except Exception:
            ent = None
        if ent:
            self._entry_set_display_mode(
                ent, new_txt, editing=(self._in_cell_focus and self.current_cell == (r, c))
            )

    # ======================= CSV I/O =======================
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

    def _sync_from_entries(self):
        """将可见 Entry 的值写回 self.data（保存前调用，防止 FocusOut 尚未触发）。"""
        if not hasattr(self, "entries"):
            return
        rows = len(self.entries)
        cols = len(self.entries[0]) if rows else 0
        if rows != len(self.data) or (rows and cols != len(self.data[0])):
            return
        for r in range(rows):
            for c in range(cols):
                try:
                    self.data[r][c] = self.entries[r][c].get()
                except Exception:
                    pass

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

        # 归一化为矩形
        max_cols = max((len(r) for r in rows), default=0)
        if max_cols == 0:
            rows = [[""]]
            max_cols = 1
        norm = [r + [""] * (max_cols - len(r)) for r in rows]

        self.data = norm
        self.current_path = path
        self.status.set(f"Opened: {os.path.basename(path)}  ({len(self.data)} x {len(self.data[0])})")
        self.current_cell = None
        self._build_grid()

    def save_csv(self):
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
        self.status.set(f"Saved: {os.path.basename(self.current_path)}")
        name = os.path.basename(self.current_path)
        self.title(f"Mini CSV - {name}  ({len(self.data)} x {len(self.data[0])})")

    # ======================= 滚动支持 =======================
    def _on_frame_configure(self, _event=None):
        self._update_scrollregion()

    def _on_canvas_configure(self, _event=None):
        self.canvas.itemconfig(self.grid_window, anchor="nw")

    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, widget):
        # Windows / Mac (legacy) / Linux(X11)
        widget.bind_all("<MouseWheel>", self._on_mousewheel)            # 垂直
        widget.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel) # 水平
        widget.bind_all("<Button-4>", self._on_mousewheel_linux)        # Linux 上
        widget.bind_all("<Button-5>", self._on_mousewheel_linux)        # Linux 下

    def _on_mousewheel(self, event):
        # Shift 在这里单独判断（但已绑定了 Shift-MouseWheel）
        if event.state & 0x0001:
            self._on_shift_mousewheel(event)
            return
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def _on_shift_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas.xview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    # ======================= 工具：省略显示与写回 =======================
    def _truncate_with_ellipsis(self, s: str) -> str:
        if s is None:
            return ""
        if len(s) <= self.display_char_limit:
            return s
        return s[: max(0, self.display_char_limit - 3)] + "..."

    def _entry_set_display_mode(self, entry: tk.Entry, full_text: str, editing: bool):
        """editing=True显示完整；False显示省略。"""
        entry.delete(0, "end")
        entry.insert(0, full_text if editing else self._truncate_with_ellipsis(full_text or ""))

    def _save_cell(self, r, c, val):
        if 0 <= r < len(self.data) and 0 <= c < len(self.data[0]):
            self.data[r][c] = val

if __name__ == "__main__":
    MiniCSV().mainloop()
