import customtkinter as ctk
from ftesc.protocol import UartCommand, build_frame, decompose_u16
from gui.styles.colors import COLORS
from gui.widgets.helpers import disable_button_temp
from ftesc.config_protocol import build_write_config_frame, SEC_DUAL
from gui.i18n import _

SECTIONS = []


def build_ui(tab_frame, panel):
    header = ctk.CTkLabel(tab_frame, text=_("lights.section_title"),
        font=ctk.CTkFont(size=15, weight='bold'), text_color=COLORS['accent_orange'])
    header.pack(pady=(12, 10))

    sec = ctk.CTkFrame(tab_frame, fg_color='transparent')
    sec.pack(fill='x', padx=20, pady=5)

    ctk.CTkLabel(sec, text=_("lights.headlight.title"),
        font=ctk.CTkFont(size=13, weight='bold'),
        text_color=COLORS['text_primary']).grid(row=0, column=0, sticky='w', pady=(8, 2))
    hl_on = ctk.BooleanVar(value=False)
    ctk.CTkSwitch(sec, text="", variable=hl_on, onvalue=True, offvalue=False,
        fg_color=COLORS['bg_light'], progress_color=COLORS['warning'],
        button_hover_color=COLORS['accent'], switch_width=36, switch_height=18
    ).grid(row=1, column=0, sticky='w', padx=(0, 10))
    ctk.CTkLabel(sec, text=_("lights.headlight.intensity"),
        font=ctk.CTkFont(size=11),
        text_color=COLORS['text_secondary']).grid(row=1, column=1, sticky='w', padx=(0, 5))
    hl_int = ctk.DoubleVar(value=100)
    hl_slider = ctk.CTkSlider(sec, from_=0, to=100, variable=hl_int,
        number_of_steps=100, button_color=COLORS['warning'], button_hover_color=COLORS['accent'],
        width=120, height=16)
    hl_slider.grid(row=1, column=2, sticky='w')
    hl_val = ctk.CTkLabel(sec, text="100%", font=ctk.CTkFont(size=10),
        text_color=COLORS['text_secondary'], width=35)
    hl_val.grid(row=1, column=3, sticky='w')
    hl_slider.configure(command=lambda v: hl_val.configure(text=f"{int(v)}%"))

    ctk.CTkLabel(sec, text=_("lights.brakelight.title"),
        font=ctk.CTkFont(size=13, weight='bold'),
        text_color=COLORS['text_primary']).grid(row=2, column=0, sticky='w', pady=(10, 2))
    bl_on = ctk.BooleanVar(value=False)
    ctk.CTkSwitch(sec, text="", variable=bl_on, onvalue=True, offvalue=False,
        fg_color=COLORS['bg_light'], progress_color=COLORS['danger'],
        button_hover_color=COLORS['accent'], switch_width=36, switch_height=18
    ).grid(row=3, column=0, sticky='w', padx=(0, 10))
    ctk.CTkLabel(sec, text=_("lights.brakelight.mode"),
        font=ctk.CTkFont(size=11),
        text_color=COLORS['text_secondary']).grid(row=3, column=1, sticky='w', padx=(0, 5))
    bl_mode = ctk.StringVar(value=_("lights.brakelight.mode_fixed"))
    ctk.CTkOptionMenu(sec, variable=bl_mode,
        values=[_("lights.brakelight.mode_fixed"), _("lights.brakelight.mode_flashing")],
        fg_color=COLORS['bg_light'], button_color=COLORS['danger'],
        font=ctk.CTkFont(size=11), width=100
    ).grid(row=3, column=2, sticky='w')

    ctk.CTkLabel(sec, text=_("lights.horn.title"),
        font=ctk.CTkFont(size=13, weight='bold'),
        text_color=COLORS['text_primary']).grid(row=4, column=0, sticky='w', pady=(10, 2))
    horn_dur = ctk.DoubleVar(value=300)
    horn_frame = ctk.CTkFrame(sec, fg_color='transparent')
    horn_frame.grid(row=5, column=0, columnspan=4, sticky='ew', pady=(0, 5))
    ctk.CTkSlider(horn_frame, from_=50, to=1000, variable=horn_dur,
        number_of_steps=95, button_color=COLORS['accent_orange'],
        button_hover_color=COLORS['accent'], width=100, height=16
    ).pack(side='left')
    dur_lbl = ctk.CTkLabel(horn_frame, text="300ms", font=ctk.CTkFont(size=10),
        text_color=COLORS['text_secondary'], width=40)
    dur_lbl.pack(side='left', padx=(5, 10))
    horn_dur.trace_add('write', lambda *a: dur_lbl.configure(text=f"{int(horn_dur.get())}ms"))
    def send_horn():
        transport = panel._get_transport()
        if not transport or not transport.is_connected:
            return
        d = int(horn_dur.get())
        payload = bytes([0, 0]) + decompose_u16(d)
        transport.send(build_frame(UartCommand.SET_BUZZER, payload))
    ctk.CTkButton(horn_frame, text=_("lights.horn.sound_button"), command=send_horn,
        fg_color=COLORS['accent_orange'], hover_color=COLORS['accent'],
        font=ctk.CTkFont(size=12, weight='bold'), height=30, width=110
    ).pack(side='left')

    ctk.CTkLabel(sec, text=_("lights.beep_on_startup"),
        font=ctk.CTkFont(size=13, weight='bold'),
        text_color=COLORS['text_primary']).grid(row=6, column=0, sticky='w', pady=(10, 2))
    bp_on = ctk.BooleanVar(value=panel._dual_config.dual_setup.beep_on_startup)
    ctk.CTkSwitch(sec, text="", variable=bp_on, onvalue=True, offvalue=False,
        fg_color=COLORS['bg_light'], progress_color=COLORS['accent_green'],
        button_hover_color=COLORS['accent'], switch_width=36, switch_height=18
    ).grid(row=7, column=0, sticky='w', padx=(0, 10))

    def do_apply():
        panel._dual_config.dual_setup.beep_on_startup = bp_on.get()
        transport = panel._get_transport()
        if transport and transport.is_connected:
            transport.send(build_write_config_frame(127, SEC_DUAL, panel._dual_config))
            mode_val = 0 if bl_mode.get() == _("lights.brakelight.mode_fixed") else 1
            payload = bytes([0, 1 if hl_on.get() else 0,
                             max(0, min(100, int(hl_int.get()))),
                             1 if bl_on.get() else 0, mode_val])
            transport.send(build_frame(UartCommand.SET_LIGHTS, payload))
        panel._set_status(_("lights.status.applied"))

    ctk.CTkButton(sec, text=_("lights.apply_button"),
        command=do_apply,
        fg_color=COLORS['accent_green'], hover_color=COLORS['success'],
        font=ctk.CTkFont(size=13, weight='bold'), height=34, width=240
    ).grid(row=8, column=0, columnspan=4, pady=(18, 10))
