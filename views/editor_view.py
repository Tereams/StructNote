from tkinter import ttk
import tkinter as tk

class EditorView(ttk.Frame):
    def __init__(self, master, on_apply):
        super().__init__(master)
        ttk.Label(self, text="Cell Editor (multi-line):", anchor="w").pack(fill="x", pady=(0,4))
        self.text = tk.Text(self, wrap="word", height=10, undo=True)
        self.text.pack(fill="both", expand=True)
        bar = ttk.Frame(self); bar.pack(fill="x", pady=(6,0))
        ttk.Button(bar, text="Apply ▶", command=on_apply).pack(side="left")
        ttk.Button(bar, text="Clear", command=lambda: self.text.delete("1.0","end")).pack(side="left", padx=6)

    def get_value(self) -> str: return self.text.get("1.0","end-1c")
    def set_value(self, s: str) -> None:
        self.text.delete("1.0","end"); self.text.insert("1.0", s or "")
