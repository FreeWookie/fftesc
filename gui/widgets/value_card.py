import customtkinter as ctk
from gui.styles.colors import COLORS


class ValueCard(ctk.CTkFrame):
    def __init__(self, parent, title="---", unit="", color=COLORS['accent'], **kwargs):
        super().__init__(parent, **kwargs)
        self._color = color
        self._unit = unit
        self._title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary'])
        self._title_label.pack(pady=(10, 0))
        self._value_label = ctk.CTkLabel(self, text="---", font=ctk.CTkFont(size=28, weight='bold'), text_color=color)
        self._value_label.pack(pady=(5, 0))
        self._unit_label = ctk.CTkLabel(self, text=unit, font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        self._unit_label.pack(pady=(0, 10))

    def set_value(self, value: float, decimals: int = 2):
        self._value_label.configure(text=f"{value:.{decimals}f}")

    def set_warning(self, is_warning: bool):
        color = COLORS['warning'] if is_warning else self._color
        self._value_label.configure(text_color=color)
