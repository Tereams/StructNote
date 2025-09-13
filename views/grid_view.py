import tkinter as tk
from tkinter import ttk
from utils.labels import col_label
from utils.text import truncate_with_ellipsis

class GridView(ttk.Frame):
    def __init__(self, master, display_limit: int, on_focus_in, on_focus_out):
        super().__init__(master)
        self.display_limit = display_limit
        self.on_focus_in = on_focus_in
        self.on_focus_out = on_focus_out

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.holder = ttk.Frame(self.canvas)
        self.win = self.canvas.create_window((0,0), window=self.holder, anchor="nw")
        self.holder.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, anchor="nw"))

        self.entries = []   # 2D Entry 引用

    def rebuild(self, data: list[list[str]], cell_px=(120,34), cell_char_w=14, cell_ipady=2):
        for w in self.holder.winfo_children(): w.destroy()
        rows = len(data); cols = len(data[0]) if rows else 0
        # 头
        corner = ttk.Label(self.holder, text="", width=6); corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        for c in range(cols):
            hdr = ttk.Frame(self.holder, borderwidth=1, relief="solid", padding=2)
            hdr.grid(row=0, column=c+1, sticky="nsew", padx=1, pady=1)
            ttk.Label(hdr, text=col_label(c), width=6).pack(side="left")

        self.entries = []
        for r in range(rows):
            rh = ttk.Frame(self.holder, borderwidth=1, relief="solid", padding=2)
            rh.grid(row=r+1, column=0, sticky="nsew", padx=1, pady=1)
            ttk.Label(rh, text=str(r+1), width=6).pack(side="left")

            row_entries = []
            for c in range(cols):
                cell = tk.Frame(self.holder, width=cell_px[0], height=cell_px[1], bd=1, relief="solid")
                cell.grid(row=r+1, column=c+1, padx=1, pady=1)
                cell.grid_propagate(False)
                e = tk.Entry(cell, width=cell_char_w)
                e.pack(fill="both", expand=True, ipady=cell_ipady)

                def _in(ev, rr=r, cc=c, ent=e):
                    self.on_focus_in(rr, cc)
                def _out(ev, rr=r, cc=c, ent=e):
                    self.on_focus_out(rr, cc, ent.get())

                e.bind("<FocusIn>", _in)
                e.bind("<FocusOut>", _out)

                # 初次展示省略
                e.insert(0, truncate_with_ellipsis(data[r][c], self.display_limit))
                row_entries.append(e)
            self.entries.append(row_entries)
