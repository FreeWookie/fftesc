import customtkinter as ctk
import tkinter
import threading
import time
from ftesc import FtescTransport, UartCommand, build_frame, FtescDualData
from ftesc.protocol import decompose_f16, decompose_f32
from ftesc.logger import FtescDataLogger
from gui.styles.colors import COLORS
from gui.widgets.helpers import enhance_scroll
from gui.i18n import _


class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, transport: FtescTransport, **kwargs):
        super().__init__(parent, **kwargs)
        self._transport = transport

        ctk.CTkLabel(self, text=_("control.section_title"),
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color=COLORS['accent_blue']).pack(pady=(15, 10), padx=15, anchor='w')
        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(0, 10))

        ctk.CTkLabel(self, text=_("control.duty_cycle_label"),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']).pack(padx=15, anchor='w')
        duty_frame = ctk.CTkFrame(self, fg_color='transparent')
        duty_frame.pack(padx=15, fill='x', pady=(2, 5))
        self._duty_var = ctk.DoubleVar(value=0.0)
        self._duty_slider = ctk.CTkSlider(duty_frame, from_=-100.0, to=100.0,
            variable=self._duty_var, number_of_steps=1000,
            button_color=COLORS['accent_blue'], button_hover_color=COLORS['accent'])
        self._duty_slider.pack(side='left', fill='x', expand=True)
        self._duty_label = ctk.CTkLabel(duty_frame, text="0.0%",
            font=ctk.CTkFont(size=12, weight='bold'),
            text_color=COLORS['accent_blue'], width=55)
        self._duty_label.pack(side='right', padx=(5, 0))
        self._duty_slider.configure(command=self._on_duty_change)
        enhance_scroll(self._duty_slider)
        ctk.CTkButton(self, text=_("control.apply_duty"), command=self._send_duty,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 10), fill='x')

        ctk.CTkLabel(self, text=_("control.motor_current_label"),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']).pack(padx=15, anchor='w')
        current_frame = ctk.CTkFrame(self, fg_color='transparent')
        current_frame.pack(padx=15, fill='x', pady=(2, 5))
        self._current_var = ctk.DoubleVar(value=0.0)
        self._current_entry = ctk.CTkEntry(current_frame, textvariable=self._current_var,
            width=80, font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_light'], border_color=COLORS['accent_blue'])
        self._current_entry.pack(side='left', fill='x', expand=True)
        self._scroll_entry(self._current_entry, self._current_var)
        ctk.CTkButton(current_frame, text=_("control.apply_icon"), command=self._send_current,
            fg_color=COLORS['accent_blue'], hover_color=COLORS['accent'],
            width=35, height=28).pack(side='right', padx=(5, 0))

        ctk.CTkLabel(self, text=_("control.brake_current_label"),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']).pack(padx=15, anchor='w', pady=(8, 0))
        brake_frame = ctk.CTkFrame(self, fg_color='transparent')
        brake_frame.pack(padx=15, fill='x', pady=(2, 5))
        self._brake_var = ctk.DoubleVar(value=0.0)
        self._brake_entry = ctk.CTkEntry(brake_frame, textvariable=self._brake_var,
            width=80, font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_light'], border_color=COLORS['accent_orange'])
        self._brake_entry.pack(side='left', fill='x', expand=True)
        self._scroll_entry(self._brake_entry, self._brake_var)
        ctk.CTkButton(brake_frame, text=_("control.brake_icon"), command=self._send_brake_current,
            fg_color=COLORS['accent_orange'], hover_color=COLORS['accent'],
            width=35, height=28).pack(side='right', padx=(5, 0))

        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(10, 10))

        self._estop_btn = ctk.CTkButton(self, text=_("control.emergency_stop"),
            command=self._emergency_stop,
            fg_color=COLORS['danger'], hover_color='#b91c1c',
            font=ctk.CTkFont(size=14, weight='bold'), height=45, corner_radius=8)
        self._estop_btn.pack(padx=15, pady=(0, 5), fill='x')

        ctk.CTkButton(self, text=_("control.read_data"), command=self._request_data,
            fg_color=COLORS['accent_green'], hover_color=COLORS['success'],
            font=ctk.CTkFont(size=12, weight='bold'), height=32).pack(padx=15, pady=(0, 5), fill='x')

        self._auto_var = ctk.BooleanVar(value=False)
        self._auto_btn = ctk.CTkButton(self, text=_("control.auto_off"),
            command=self._toggle_auto_read,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_green'],
            font=ctk.CTkFont(size=11), height=28)
        self._auto_btn.pack(padx=15, pady=(0, 5), fill='x')

        self._log_btn = ctk.CTkButton(self, text=_("control.log_off"),
            command=self._toggle_logging,
            fg_color=COLORS['bg_light'], hover_color=COLORS['danger'],
            font=ctk.CTkFont(size=11), height=28)
        self._log_btn.pack(padx=15, pady=(0, 5), fill='x')

        ctk.CTkButton(self, text=_("control.reboot"), command=self._reboot,
            fg_color=COLORS['bg_light'], hover_color=COLORS['danger'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(5, 0), fill='x')

        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(8, 6))
        peri_frame = ctk.CTkFrame(self, fg_color='transparent')
        peri_frame.pack(fill='x', padx=15, pady=(0, 15))
        self._headlight_btn = ctk.CTkButton(peri_frame, text=_("control.headlight"),
            command=lambda: self._send_peri(UartCommand.SET_HEADLIGHT),
            fg_color=COLORS['bg_light'], hover_color=COLORS['warning'],
            font=ctk.CTkFont(size=11), height=28, width=70)
        self._headlight_btn.pack(side='left', padx=(0, 5))
        self._brakelight_btn = ctk.CTkButton(peri_frame, text=_("control.brakelight"),
            command=lambda: self._send_peri(UartCommand.SET_BRAKELIGHT),
            fg_color=COLORS['bg_light'], hover_color=COLORS['danger'],
            font=ctk.CTkFont(size=11), height=28, width=70)
        self._brakelight_btn.pack(side='left', padx=(0, 5))
        ctk.CTkButton(peri_frame, text=_("control.horn"),
            command=lambda: self._send_peri(UartCommand.SET_BUZZER),
            fg_color=COLORS['accent_orange'], hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=11), height=28, width=80).pack(side='left')
        self._peri_states: dict = {UartCommand.SET_HEADLIGHT: False,
                                   UartCommand.SET_BRAKELIGHT: False}

        self._auto_reading = False
        self._auto_thread = None
        self._logger = FtescDataLogger()
        self._logging = False
        self.on_log_data = None

    def _scroll_entry(self, entry, var, step=1.0):
        target = entry._entry if hasattr(entry, '_entry') else entry
        def on_wheel(event):
            try:
                val = var.get()
            except (ValueError, tkinter.TclError):
                val = 0.0
            if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
                var.set(val + step)
            elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
                var.set(val - step)
        target.bind("<Button-4>", on_wheel)
        target.bind("<Button-5>", on_wheel)
        target.bind("<MouseWheel>", on_wheel)

    def _on_duty_change(self, value):
        self._duty_label.configure(text=f"{value:.1f}%")

    def _send_duty(self):
        if not self._transport.is_connected: return
        duty = self._duty_var.get()
        payload = decompose_f16(duty / 100.0, 10000.0)
        frame = build_frame(UartCommand.SET_DUTY, payload)
        self._transport.send(frame)

    def _send_current(self):
        if not self._transport.is_connected: return
        current = self._current_var.get()
        payload = decompose_f32(current, 1000000.0)
        frame = build_frame(UartCommand.SET_CURRENT, payload)
        self._transport.send(frame)

    def _send_brake_current(self):
        if not self._transport.is_connected: return
        brake = self._brake_var.get()
        payload = decompose_f32(brake, 1000000.0)
        frame = build_frame(UartCommand.SET_BRAKE_CURRENT, payload)
        self._transport.send(frame)

    def _request_data(self):
        if not self._transport.is_connected: return
        frame = build_frame(UartCommand.OBTAIN_DATA_ONCE, b'')
        self._transport.send(frame)

    def _toggle_auto_read(self):
        self._auto_reading = not self._auto_reading
        if self._auto_reading:
            self._auto_btn.configure(text=_("control.auto_on"),
                fg_color=COLORS['accent_green'], hover_color=COLORS['success'])
            self._auto_thread = threading.Thread(target=self._auto_read_loop, daemon=True)
            self._auto_thread.start()
        else:
            self._auto_btn.configure(text=_("control.auto_off"),
                fg_color=COLORS['bg_light'], hover_color=COLORS['accent_green'])

    def _auto_read_loop(self):
        while self._auto_reading and self._transport.is_connected:
            self._request_data()
            time.sleep(0.1)

    def _toggle_logging(self):
        if not self._logging:
            self._logger = FtescDataLogger()
            if self._logger.start():
                self._logging = True
                self._log_btn.configure(text=_("control.log_on"),
                    fg_color=COLORS['danger'], hover_color='#b91c1c')
                print(f"[LOG] D\u00e9but enregistrement: {self._logger.filepath}")
            else:
                print("[LOG] \u00c9chec d\u00e9marrage")
        else:
            self._logger.stop()
            self._logging = False
            self._log_btn.configure(text=_("control.log_off"),
                fg_color=COLORS['bg_light'], hover_color=COLORS['danger'])
            print(f"[LOG] Fin enregistrement: {self._logger.row_count} lignes")

    def log_data(self, dual_data):
        if self._logging and self._logger and self._logger.is_running:
            self._logger.log_dual(dual_data)

    def _reboot(self):
        if not self._transport.is_connected: return
        frame = build_frame(UartCommand.REBOOT_FTESC, b'')
        self._transport.send(frame)

    def _emergency_stop(self):
        if not self._transport.is_connected: return
        payload = decompose_f16(0.0, 10000.0)
        frame = build_frame(UartCommand.SET_DUTY, payload)
        self._transport.send(frame)
        self._duty_var.set(0.0)
        self._duty_label.configure(text="0.0%")

    def _send_peri(self, cmd: UartCommand):
        if not self._transport.is_connected: return
        if cmd == UartCommand.SET_BUZZER:
            payload = bytes([0, 200 >> 8, 200 & 0xFF])
            frame = build_frame(cmd, payload)
            self._transport.send(frame)
            return
        val = self._peri_states.get(cmd, False)
        self._peri_states[cmd] = not val
        payload = bytes([0, 1 if not val else 0])
        frame = build_frame(cmd, payload)
        self._transport.send(frame)
        btn = self._headlight_btn if cmd == UartCommand.SET_HEADLIGHT else self._brakelight_btn
        btn.configure(fg_color=COLORS['warning'] if not val else COLORS['bg_light'])
