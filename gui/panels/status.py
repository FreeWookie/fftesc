import customtkinter as ctk
import webbrowser
from ftesc import ConnectionState
from gui.styles.colors import COLORS
from gui.i18n import _


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, **kwargs)
        self._state_label = ctk.CTkLabel(self, text=_("status.disconnected"),
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        self._state_label.pack(side='left', padx=10)
        self._stats_label = ctk.CTkLabel(self, text=_("status.stats_placeholder"),
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        self._stats_label.pack(side='right', padx=10)

    def update_connection(self, state: ConnectionState, message: str):
        self._state_label.configure(text=f"{state.value} \u2014 {message}")

    def update_stats(self, stats: dict):
        self._stats_label.configure(
            text=_("status.stats_format").format(**stats))

    def show_message(self, msg: str, timeout_ms: int = 4000):
        old = self._state_label.cget("text")
        self._state_label.configure(text=msg, text_color=COLORS['accent_blue'])
        self.after(timeout_ms,
            lambda: self._state_label.configure(text=old, text_color=COLORS['text_secondary']))

    def add_donation_buttons(self):
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(side='right', padx=10)
        self.btn_lumo = ctk.CTkButton(btn_frame, text=_("status.donate.lumo"),
            command=self._donate_lumo,
            fg_color=COLORS['mauve'], hover_color=COLORS['mauve_hover'],
            font=ctk.CTkFont(size=10), height=22, corner_radius=5, width=80)
        self.btn_lumo.pack(side='left', padx=(5, 0))
        self.btn_skate = ctk.CTkButton(btn_frame, text=_("status.donate.wook"),
            command=self._donate_wook,
            fg_color=COLORS['mauve'], hover_color=COLORS['mauve_hover'],
            font=ctk.CTkFont(size=10), height=22, corner_radius=5, width=80)
        self.btn_skate.pack(side='left', padx=(5, 0))

    def _donate_lumo(self):
        webbrowser.open("https://proton.me/donate")

    def _donate_wook(self):
        btc_address = "bc1quw8zmz63jzgts7rcn7hmjsxfezhgat3ck35ptc"
        dialog = ctk.CTkInputDialog(
            text=_("status.donate.wook_text").format(address=btc_address),
            title=_("status.donate.wook_title"))
        dialog.mainloop()
