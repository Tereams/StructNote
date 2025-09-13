from views.main_window import MainWindow
from views.grid_view import GridView
from views.editor_view import EditorView
from controller import AppController

def main():
    win = MainWindow()
    editor = EditorView(win.right, on_apply=lambda: ctrl.on_apply_from_editor())
    editor.pack(fill="both", expand=True)
    grid = GridView(win.left, display_limit=20,
                    on_focus_in=lambda r,c: ctrl.on_cell_focus_in(r,c),
                    on_focus_out=lambda r,c,text: ctrl.on_cell_focus_out(r,c,text))
    grid.pack(fill="both", expand=True)

    global ctrl
    ctrl = AppController(win, grid, editor)
    win.mainloop()

if __name__ == "__main__":
    main()
