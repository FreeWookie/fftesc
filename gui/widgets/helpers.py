def disable_button_temp(button, duration_ms=1500, busy_text="\u23f3 Envoi..."):
    orig_text = button.cget("text")
    orig_fg = button.cget("fg_color")
    orig_hover = button.cget("hover_color")
    try:
        button.configure(state="disabled", text=busy_text,
            fg_color=("grey60", "grey30"), hover_color=("grey60", "grey30"))
    except Exception:
        return
    def restore():
        try:
            button.configure(state="normal", text=orig_text,
                fg_color=orig_fg, hover_color=orig_hover)
        except Exception:
            pass
    button.after(duration_ms, restore)


def enhance_scroll(widget):
    """Force la sensibilité de la molette sur les widgets CTkSlider."""
    if hasattr(widget, '_entry'):
        target = widget._entry
    else:
        target = getattr(widget, '_canvas', widget)

    def on_mousewheel(event):
        step = 1.0
        orig = widget.get()
        to_val = widget.cget('to')
        from_val = widget.cget('from_')
        if event.num == 4:
            widget.set(min(to_val, orig + step))
        elif event.num == 5:
            widget.set(max(from_val, orig - step))
        elif event.delta > 0:
            widget.set(min(to_val, orig + step))
        elif event.delta < 0:
            widget.set(max(from_val, orig - step))

    target.bind("<Button-4>", on_mousewheel)
    target.bind("<Button-5>", on_mousewheel)
    target.bind("<MouseWheel>", on_mousewheel)
