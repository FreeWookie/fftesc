import customtkinter as ctk
from gui.styles.colors import COLORS


class FaultIndicator(ctk.CTkFrame):
    def __init__(self, parent, label="D\u00e9faut", **kwargs):
        super().__init__(parent, **kwargs)
        self._indicator = ctk.CTkLabel(self, text="\u25cf", font=ctk.CTkFont(size=18), text_color=COLORS['success'])
        self._indicator.pack(side='left', padx=(10, 5))
        self._label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=13), text_color=COLORS['text_secondary'])
        self._label.pack(side='left', padx=(0, 10))

    def set_fault(self, active: bool):
        if active:
            self._indicator.configure(text_color=COLORS['danger'])
            self._label.configure(text_color=COLORS['danger'])
        else:
            self._indicator.configure(text_color=COLORS['success'])
            self._label.configure(text_color=COLORS['text_secondary'])
