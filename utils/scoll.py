def bind_mousewheel(widget, on_v, on_h):
    widget.bind_all("<MouseWheel>", lambda e: on_v(-1 if e.delta > 0 else 1))
    widget.bind_all("<Shift-MouseWheel>", lambda e: on_h(-1 if e.delta > 0 else 1))
    widget.bind_all("<Button-4>", lambda e: on_v(-1))
    widget.bind_all("<Button-5>", lambda e: on_v(1))
