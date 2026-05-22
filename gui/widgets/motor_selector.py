import customtkinter as ctk
from gui.styles.colors import COLORS
from gui.i18n import _


class MotorSelector(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._var = ctk.StringVar(value="both")
        ctk.CTkLabel(self, text="\u26a1", font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 4))
        seg = ctk.CTkSegmentedButton(self, values=[_("motor_selector.motor_a"), _("motor_selector.motor_b"), _("motor_selector.both")],
            variable=self._var, dynamic_resizing=False,
            fg_color=COLORS['bg_light'],
            selected_color=COLORS['accent_blue'], selected_hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=11), height=28)
        seg.pack(side='left', fill='x', expand=True)

    def get(self) -> str:
        val = self._var.get()
        if val == _("motor_selector.motor_a"):
            return "A"
        elif val == _("motor_selector.motor_b"):
            return "B"
        return "both"
