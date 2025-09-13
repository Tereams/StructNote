from tkinter import filedialog, messagebox
from model.sheet import Sheet
from services.csv_service import load_csv, save_csv
from utils.text import truncate_with_ellipsis

class AppController:
    def __init__(self, main_window, grid_view, editor_view):
        self.win = main_window
        self.grid = grid_view
        self.editor = editor_view
        self.sheet = Sheet()
        self.current_path: str | None = None
        self._in_cell_focus = False
        self.display_limit = 20

        # 初次构建网格
        self._refresh_grid()

        # 菜单
        self._build_menu()

    # 视图事件回调
    def on_cell_focus_in(self, r: int, c: int):
        self.sheet.current_cell = (r, c)
        self._in_cell_focus = True
        self._set_entry_text(r, c, self.sheet.get(r,c), editing=True)
        self._load_editor_from_cell(r, c)

    def on_cell_focus_out(self, r: int, c: int, text: str):
        self._in_cell_focus = False
        self.sheet.set(r, c, text)
        self._set_entry_text(r, c, self.sheet.get(r,c), editing=False)
        if self.sheet.current_cell == (r, c):
            self._load_editor_from_cell(r, c)

    def on_apply_from_editor(self):
        if not self.sheet.current_cell:
            self.win.status_var.set("No cell selected."); return
        r, c = self.sheet.current_cell
        txt = self.editor.get_value()
        self.sheet.set(r, c, txt)
        self._set_entry_text(r, c, txt, editing=self._in_cell_focus)
        self.win.status_var.set(f"Updated cell ({r+1}, {c+1}) from editor.")

    # 文件
    def open_csv(self):
        path = filedialog.askopenfilename(title="Open CSV",
                                          filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path: return
        try:
            data = load_csv(path)
        except Exception as e:
            messagebox.showerror("Open CSV Failed", f"{e}"); return
        self.sheet.replace_all(data)
        self.current_path = path
        self.win.status_var.set(f"Opened: {path}")
        self._refresh_grid()

    def save_csv(self):
        if not self.current_path: return self.save_csv_as()
        try:
            save_csv(self.current_path, self.sheet.to_list())
        except Exception as e:
            messagebox.showerror("Save CSV Failed", f"{e}"); return
        self.win.status_var.set(f"Saved: {self.current_path}")

    def save_csv_as(self):
        path = filedialog.asksaveasfilename(title="Save CSV As",
                                            defaultextension=".csv",
                                            filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path: return
        self.current_path = path
        self.save_csv()

    # 内部
    def _build_menu(self):
        import tkinter as tk
        m = tk.Menu(self.win)
        filemenu = tk.Menu(m, tearoff=False)
        filemenu.add_command(label="Open...    Ctrl+O", command=self.open_csv)
        filemenu.add_command(label="Save       Ctrl+S", command=self.save_csv)
        filemenu.add_command(label="Save As...", command=self.save_csv_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.win.destroy)
        m.add_cascade(label="File", menu=filemenu)
        self.win.config(menu=m)
        self.win.bind_all("<Control-o>", lambda e: self.open_csv())
        self.win.bind_all("<Control-s>", lambda e: self.save_csv())

    def _refresh_grid(self):
        data = self.sheet.to_list()
        self.grid.rebuild(data)
        # 标题
        name = (self.current_path or "Untitled").split("/")[-1]
        r, c = self.sheet.shape()
        self.win.title(f"Mini CSV - {name}  ({r} x {c})")

    def _set_entry_text(self, r: int, c: int, full_text: str, editing: bool):
        try:
            ent = self.grid.entries[r][c]
        except Exception:
            return
        ent.delete(0, "end")
        ent.insert(0, full_text if editing else truncate_with_ellipsis(full_text, self.display_limit))

    def _load_editor_from_cell(self, r: int, c: int):
        self.editor.set_value(self.sheet.get(r, c))
