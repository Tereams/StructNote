import tkinter as tk
from tkinter import ttk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini CSV")
        self.geometry("1200x700")
        self.status_var = tk.StringVar(value="Ready")

        self.pane = tk.PanedWindow(self, orient="horizontal")
        self.pane.pack(fill="both", expand=True)

        self.left = ttk.Frame(self.pane)
        self.right = ttk.Frame(self.pane, padding=6)
        self.pane.add(self.left, stretch="always")
        self.pane.add(self.right, width=420)

        # 底部状态栏
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill="x", side="bottom")
