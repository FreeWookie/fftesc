import customtkinter as ctk
import threading
import time
import random
import tkinter.filedialog as filedialog
from typing import Optional, Callable
from ftesc import (
    FtescTransport, ConnectionState, SerialConfig,
    FtescDualData, FtescRealtimeData, UartCommand, build_frame,
)
from ftesc.simulator import FtescSimulator
from ftesc.replay import CsvReplayThread
from gui.styles.colors import COLORS
from gui.i18n import _


class PortMonitor(threading.Thread):
    def __init__(self, on_ports_changed: Callable, **kwargs):
        super().__init__(daemon=True, **kwargs)
        self._on_ports_changed = on_ports_changed
        self._running = True
        self._known: set = set()

    def run(self):
        while self._running:
            try:
                import serial.tools.list_ports as list_ports
                ports = list_ports.comports()
                current = {p.device for p in ports}
                new_ports = current - self._known
                if new_ports and self._known:
                    self._on_ports_changed(new_ports)
                self._known = current
            except Exception:
                pass
            time.sleep(2.0)

    def stop(self):
        self._running = False


class ConnectionPanel(ctk.CTkFrame):
    def __init__(self, parent, transport: FtescTransport, **kwargs):
        super().__init__(parent, **kwargs)
        self._transport = transport
        self._simulating = False
        self._sim_instance: Optional[FtescSimulator] = None
        self.on_sim_data: Optional[Callable] = None
        self.on_replay_data: Optional[Callable] = None
        self.on_status_message: Optional[Callable] = None
        self.on_simulator_state_changed: Optional[Callable[[bool], None]] = None

        ctk.CTkLabel(self, text=_("connection.section_title"),
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color=COLORS['accent']).pack(pady=(10, 10), padx=15, anchor='w')
        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(0, 10))

        ctk.CTkLabel(self, text=_("connection.serial_port_label"),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']).pack(padx=15, anchor='w')

        self._port_var = ctk.StringVar(value=_("connection.port_auto"))
        self._port_menu = ctk.CTkOptionMenu(self, variable=self._port_var,
            values=[_("connection.port_auto")],
            fg_color=COLORS['bg_light'], button_color=COLORS['accent'],
            font=ctk.CTkFont(size=12))
        self._port_menu.pack(padx=15, pady=(2, 4), fill='x')

        ctk.CTkButton(self, text=_("connection.refresh_ports"),
            command=self._refresh_ports,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 8), fill='x')

        ctk.CTkLabel(self, text=_("connection.baud_rate_label"),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']).pack(padx=15, anchor='w')

        self._baud_var = ctk.StringVar(value="115200")
        self._baud_menu = ctk.CTkOptionMenu(self, variable=self._baud_var,
            values=["9600", "19200", "38400", "57600", "115200", "230400", "921600"],
            fg_color=COLORS['bg_light'], button_color=COLORS['accent'],
            font=ctk.CTkFont(size=12))
        self._baud_menu.pack(padx=15, pady=(2, 8), fill='x')

        self._connect_btn = ctk.CTkButton(self, text=_("connection.connect_button"),
            command=self._toggle_connection,
            fg_color=COLORS['accent_green'], hover_color=COLORS['success'],
            font=ctk.CTkFont(size=13, weight='bold'), height=38)
        self._connect_btn.pack(padx=15, pady=(0, 5), fill='x')

        self._status_label = ctk.CTkLabel(self, text=_("connection.status.disconnected"),
            font=ctk.CTkFont(size=12), text_color=COLORS['danger'])
        self._status_label.pack(pady=(0, 5))

        self._sim_btn = ctk.CTkButton(self, text=_("connection.simulator.mode"),
            command=self._toggle_simulator,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=11), height=28)
        self._sim_btn.pack(padx=15, pady=(0, 4), fill='x')

        self._replay_btn = ctk.CTkButton(self, text=_("connection.replay_csv"),
            command=self._toggle_replay,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_orange'],
            font=ctk.CTkFont(size=11), height=28)
        self._replay_btn.pack(padx=15, pady=(0, 4), fill='x')

        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(4, 6))
        self._scan_btn = ctk.CTkButton(self, text=_("connection.scan_escs"),
            command=self._request_scan,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=11), height=28)
        self._scan_btn.pack(padx=15, pady=(0, 4), fill='x')
        self._scan_results_frame = ctk.CTkFrame(self, fg_color='transparent')
        self._scan_results_frame.pack(padx=15, pady=(0, 6), fill='x')
        self._scan_results_label = ctk.CTkLabel(
            self._scan_results_frame, text="",
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
            justify='left', anchor='w')
        self._scan_results_label.pack(fill='x')

        self._replay_thread: Optional[CsvReplayThread] = None
        self._monitor: Optional[PortMonitor] = None
        self.on_scan_request: Optional[Callable] = None   # public — câblé par app.py
        self._start_monitor()

    def _start_monitor(self):
        self._monitor = PortMonitor(self._on_new_ports)
        self._monitor.start()

    def destroy_monitor(self):
        if self._monitor:
            self._monitor.stop()
            self._monitor = None

    def _on_new_ports(self, new_ports: set):
        names = ", ".join(sorted(new_ports))
        if self.on_status_message:
            self.on_status_message(_("connection.new_port_detected").format(names=names))
        self._refresh_ports()

    def _update_for_new_ports(self, *args):
        self._refresh_ports()

    def _refresh_ports(self):
        try:
            import serial.tools.list_ports as list_ports
            ports = list_ports.comports()
            items = [p.device for p in ports]
        except Exception:
            items = []
        if not items:
            items = [_("connection.no_port")]
        auto_text = _("connection.port_auto")
        values = [auto_text] + items
        self._port_menu.configure(values=values)
        self._port_var.set(auto_text)
        self._try_auto_select(items)

    def _try_auto_select(self, items: list):
        try:
            import serial.tools.list_ports as list_ports
        except ImportError:
            return
        for p in list_ports.comports():
            if p.vid in (0x1A86, 0x10C4, 0x0403, 0x2E3C) and p.device in items:
                self._port_var.set(p.device)
                return

    def _toggle_connection(self):
        if self._transport.is_connected:
            self._transport.disconnect()
            return
        port = self._port_var.get()
        if port == _("connection.port_auto") or port == _("connection.no_port"):
            port = ""
        baud = int(self._baud_var.get())
        config = SerialConfig(port=port, baudrate=baud)
        self._transport.connect(config)

    def update_state(self, state: ConnectionState, message: str):
        state_map = {
            ConnectionState.DISCONNECTED: (_("connection.status.disconnected"), COLORS['danger']),
            ConnectionState.CONNECTING: (_("connection.status.connecting"), COLORS['warning']),
            ConnectionState.CONNECTED: (_("connection.status.connected"), COLORS['success']),
            ConnectionState.ERROR: (_("connection.status.error"), COLORS['danger']),
            ConnectionState.RECONNECTING: (_("connection.status.reconnecting"), COLORS['warning']),
        }
        text, color = state_map.get(state,
            (_("connection.status.unknown"), COLORS['text_secondary']))
        self._status_label.configure(text=text, text_color=color)
        if state == ConnectionState.CONNECTED:
            self._connect_btn.configure(text=_("connection.disconnect_button"),
                fg_color=COLORS['accent'], hover_color=COLORS['danger'])
        else:
            self._connect_btn.configure(text=_("connection.connect_button"),
                fg_color=COLORS['accent_green'], hover_color=COLORS['success'])

    def _toggle_simulator(self):
        if self._simulating:
            if self._sim_instance:
                self._sim_instance.stop()
                self._sim_instance = None
            self._simulating = False
            self._sim_btn.configure(text=_("connection.simulator.mode"),
                fg_color=COLORS['bg_light'])
            self._status_label.configure(text=_("connection.simulator.stopped"),
                text_color=COLORS['text_secondary'])
            if self.on_simulator_state_changed:
                self.on_simulator_state_changed(False)
        else:
            self._sim_instance = FtescSimulator()
            self._sim_instance.on_data = self._on_sim_data
            self._sim_instance.start()
            self._simulating = True
            self._sim_btn.configure(text=_("connection.simulator.stop"),
                fg_color=COLORS['warning'])
            self._status_label.configure(text=_("connection.simulator.active"),
                text_color=COLORS['accent_blue'])
            if self.on_simulator_state_changed:
                self.on_simulator_state_changed(True)
            # Scan auto pour peupler le firmware dès le démarrage du simulateur
            if self.on_scan_request:
                self.on_scan_request()

    def _on_sim_data(self, dual_data):
        if self.on_sim_data:
            self.on_sim_data(dual_data)
        if hasattr(self, '_replay_thread') and self._replay_thread:
            return
        self._update_replay_data(dual_data)

    def _toggle_replay(self):
        if self._replay_thread and self._replay_thread.is_alive():
            self._replay_thread.stop()
            self._replay_thread = None
            self._replay_btn.configure(text=_("connection.replay_csv"),
                fg_color=COLORS['bg_light'])
            return
        path = filedialog.askopenfilename(
            filetypes=[(_("connection.filetype.csv"), "*.csv"),
                       (_("connection.filetype.all"), "*.*")],
            title=_("connection.replay.file_dialog_title"))
        if not path:
            return
        self._replay_thread = CsvReplayThread(path, self._on_replay_line)
        self._replay_thread.start()
        self._replay_btn.configure(text=_("connection.replay.stop"),
            fg_color=COLORS['danger'])

    def _on_replay_line(self, dual_data):
        if self.on_replay_data:
            self.on_replay_data(dual_data)
        self._update_replay_data(dual_data)

    def _update_replay_data(self, dual_data):
        pass

    def _request_scan(self):
        self._scan_btn.configure(text=_("connection.scanning"), state='disabled')
        self._scan_results_label.configure(text="")
        if self.on_scan_request:
            self.on_scan_request()

    def show_discovered_escs(self, escs: dict):
        self._scan_btn.configure(text=_("connection.scan_escs"), state='normal')
        if not escs:
            self._scan_results_label.configure(
                text=_("connection.esc_not_found"),
                text_color=COLORS['danger'])
            return
        lines = []
        for ctrl_id in sorted(escs.keys()):
            info = escs[ctrl_id]
            lines.append(
                _("connection.esc_id_format").format(
                    id=ctrl_id, version=info.version_string, model=info.model_name))
        self._scan_results_label.configure(
            text=_("connection.escs_found").format(count=len(escs)) + "\n" + "\n".join(lines),
            text_color=COLORS['success'])

    def _toggle_theme(self):
        pass
