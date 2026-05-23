import customtkinter as ctk
from ftesc import FtescRealtimeData, FtescFault, FtescFirmwareInfo
from gui.styles.colors import COLORS
from gui.widgets.chart_card import ChartCard
from gui.i18n import _

# Constantes de routage moteur — utilisées dans tout le projet
MOTOR_LABEL_A = "Moteur A"
MOTOR_LABEL_B = "Moteur B"


class RealtimeDataPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._cards_a: dict = {}
        self._cards_b: dict = {}

        scroll = ctk.CTkScrollableFrame(self, fg_color='transparent')
        scroll.pack(fill='both', expand=True)

        self._build_motor_section(scroll, "A", COLORS['accent_blue'])
        ctk.CTkFrame(scroll, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=10, pady=8)
        self._build_motor_section(scroll, "B", COLORS['accent_green'])

    def _build_motor_section(self, parent, suffix: str, accent: str):
        header = ctk.CTkFrame(parent, fg_color=COLORS['bg_medium'], height=36)
        header.pack(fill='x', padx=10, pady=(8, 0))
        header.pack_propagate(False)

        title = ctk.CTkLabel(header,
            text=_("realtime.motor_title").format(suffix=suffix),
            font=ctk.CTkFont(size=14, weight='bold'), text_color=accent)
        title.pack(side='left', padx=(12, 8))

        id_label = ctk.CTkLabel(header, text=_("realtime.id_esc_placeholder"),
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        id_label.pack(side='left', padx=4)

        fw_label = ctk.CTkLabel(header, text=_("realtime.fw_placeholder"),
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        fw_label.pack(side='right', padx=12)

        charts = ctk.CTkFrame(parent, fg_color='transparent')
        charts.pack(fill='x', padx=10, pady=5)
        charts.grid_columnconfigure((0, 1), weight=1)
        titles = [
            (_("realtime.chart.voltage"), _("realtime.chart.voltage_unit"), "voltage"),
            (_("realtime.chart.current"), _("realtime.chart.current_unit"), "current"),
            (_("realtime.chart.rpm"), _("realtime.chart.rpm_unit"), "rpm"),
            (_("realtime.chart.temp_fet"), _("realtime.chart.temp_fet_unit"), "temp_fet"),
            (_("realtime.chart.temp_motor"), _("realtime.chart.temp_motor_unit"), "temp_motor"),
            (_("realtime.chart.duty"), _("realtime.chart.duty_unit"), "duty"),
        ]
        cards = {}
        for i, (title, unit, key) in enumerate(titles):
            col = i % 2
            r = i // 2
            card = ChartCard(charts, title, unit, key, accent)
            card.grid(row=r, column=col, padx=5, pady=5, sticky='ew')
            cards[key] = card
        fault_frame = ctk.CTkFrame(parent, fg_color='transparent')
        fault_frame.pack(fill='x', padx=10, pady=(0, 5))
        fault_label = ctk.CTkLabel(fault_frame, text=_("realtime.fault.none"),
            text_color=COLORS['success'])
        fault_label.pack()
        cards['_fault_label'] = fault_label

        if suffix == "A":
            self._cards_a = cards
            self._header_a = (id_label, fw_label)
        else:
            self._cards_b = cards
            self._header_b = (id_label, fw_label)

    def refresh_theme(self):
        for card in self._cards_a.values():
            if hasattr(card, 'refresh_theme'):
                card.refresh_theme()
        for card in self._cards_b.values():
            if hasattr(card, 'refresh_theme'):
                card.refresh_theme()

    def update_motor_data(self, motor_id: str, data: FtescRealtimeData):
        cards = self._cards_a if motor_id == MOTOR_LABEL_A else self._cards_b
        if not cards:
            return
        header = self._header_a if motor_id == MOTOR_LABEL_A else self._header_b
        if header:
            id_label, fw_label = header
            id_label.configure(text=_("realtime.id_esc_format").format(id=data.controller_id))
            if data.firmware_version:
                fw_label.configure(
                    text=_("realtime.fw_format").format(version=data.firmware_version))
        mapping = {
            "voltage": data.inp_voltage,
            "current": data.motor_current,
            "rpm": data.rpm,
            "temp_fet": data.temp_fet,
            "temp_motor": data.temp_motor,
            "duty": data.duty_cycle_now * 100.0,
        }
        for key, value in mapping.items():
            if key in cards:
                cards[key].set_value(value)
        if '_fault_label' in cards:
            if data.fault == 0:
                cards['_fault_label'].configure(text=_("realtime.fault.none"),
                    text_color=COLORS['success'])
            else:
                faults = FtescFault.decode(data.fault)
                cards['_fault_label'].configure(text=", ".join(faults),
                    text_color=COLORS['danger'])

    def update_firmware_info(self, motor_id: str, fw_info: FtescFirmwareInfo):
        header = self._header_a if motor_id == MOTOR_LABEL_A else self._header_b
        if header:
            motor_label, fw_label = header
            fw_label.configure(
                text=_("realtime.fw_info_format").format(
                    version=fw_info.version_string, model=fw_info.model_name))
