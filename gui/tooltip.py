# -*- coding: utf-8 -*-
# gui/tooltip.py
import customtkinter as ctk
from gui.styles.colors import COLORS

class TooltipManager:
    """Gestionnaire singleton pour les tooltips."""
    
    _instance = None
    _tooltip_window = None
    _tooltip_label = None
    _current_widget = None
    _delay_ms = 500
    _timer_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tooltip_window = None
        self._tooltip_label = None

    def _ensure_window(self):
        """Crée la fenêtre tooltip au premier besoin (lazy)."""
        if self._tooltip_window is not None:
            return
        self._tooltip_window = ctk.CTkToplevel()
        self._tooltip_window.withdraw()
        self._tooltip_window.overrideredirect(True)
        self._tooltip_window.attributes('-topmost', True)
        self._tooltip_window.configure(fg_color=COLORS['bg_medium'])
        
        self._tooltip_label = ctk.CTkLabel(
            self._tooltip_window,
            text="",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_primary'],
            wraplength=250,
            padx=10,
            pady=5
        )
        self._tooltip_label.pack()

    def show(self, widget, text):
        """Affiche le tooltip au-dessus du widget."""
        if not text:
            self.hide()
            return
        self._ensure_window()

        # Si on change de widget, on reset le timer
        if self._current_widget != widget:
            if self._timer_id:
                self._tooltip_window.after_cancel(self._timer_id)
            self._timer_id = self._tooltip_window.after(self._delay_ms, lambda: self._do_show(widget, text))
            self._current_widget = widget
        else:
            # Si on reste sur le même widget, on s'assure qu'il est visible
            if self._tooltip_window.state() == 'withdrawn':
                self._do_show(widget, text)

    def _do_show(self, widget, text):
        """Affiche réellement le tooltip."""
        self._ensure_window()
        self._tooltip_label.configure(text=text)
        
        # Positionner au-dessus du widget
        x = widget.winfo_rootx() + widget.winfo_width() + 10
        y = widget.winfo_rooty()
        
        # Vérifier les limites de l'écran (simple)
        screen_width = self._tooltip_window.winfo_screenwidth()
        if x + 250 > screen_width:
            x = widget.winfo_rootx() - 260
        
        self._tooltip_window.geometry(f"+{x}+{y}")
        self._tooltip_window.deiconify()

    def hide(self):
        """Cache le tooltip."""
        if not self._tooltip_window:
            return
        if self._timer_id:
            self._tooltip_window.after_cancel(self._timer_id)
            self._timer_id = None
        self._tooltip_window.withdraw()

    def bind(self, widget, text):
        """Lie un tooltip à un widget."""
        widget.bind("<Enter>", lambda e: self.show(widget, text))
        widget.bind("<Leave>", lambda e: self.hide())