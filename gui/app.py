# -*- coding: utf-8 -*-
"""
gui/app.py — Point d'entrée de l'interface graphique FFTESC
"""

import customtkinter as ctk
import tkinter.messagebox as tkmb
from typing import Optional
import json
import os

from ftesc import (
    FtescTransport, ConnectionState, FtescRealtimeData, FtescFirmwareInfo,
    FtescDualData,
    UartCommand, parse_frame, parse_realtime_data, parse_firmware_info,
    build_frame, build_obtain_all_ids_frame,
)
from ftesc.config_protocol import parse_config_response, SECTION_NAMES
from ftesc.profiles import save_profile, load_profile, list_profiles, delete_profile, export_profile, import_profile
from gui.styles.colors import COLORS
from gui.panels.connection import ConnectionPanel
from gui.panels.control import ControlPanel
from gui.panels.realtime import RealtimeDataPanel, MOTOR_LABEL_A, MOTOR_LABEL_B
from gui.panels.config_panel import ConfigPanel
from gui.panels.profile import ProfilePanel
from gui.panels.status import StatusBar
from gui.panels.wizard_panel import WizardPanel
from gui.panels.recovery import RecoveryPanel
from gui.app_icons import (
    apply_window_icons, make_title_ctk_image, make_logo_ctk_image,
    make_connection_indicator_images, update_connection_indicator,
)


class FftescApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._destroyed = False
        self.title("FFTESC \u2014 Free FTESC Tool")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS['bg_dark'])
        self._theme_config_path = os.path.expanduser("~/.fftesc_tool_config.json")
        theme = self._load_theme_config()
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme('dark-blue')

        self._transport = FtescTransport()
        self._transport.on_connection_changed = self._on_connection_changed
        self._transport.on_data_received = self._on_raw_data
        self._transport.on_error = self._on_error
        self._last_data: Optional[FtescRealtimeData] = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = ctk.CTkScrollableFrame(self, width=250, fg_color=COLORS['bg_medium'], corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky='ns')

        # ── Logo titre en haut de la sidebar (indicateur visuel connexion) ──────
        # Pré-charge les deux états off / on pour un swap sans latence
        self._logo_images = make_connection_indicator_images(200, 54)
        self._logo_label: Optional[ctk.CTkLabel] = None

        _off_img = self._logo_images.get("disconnected")
        if _off_img:
            self._logo_label = ctk.CTkLabel(
                self._sidebar,
                image=_off_img,
                text="",
                fg_color="transparent",
            )
            self._logo_label.pack(pady=(10, 4), padx=10)
        else:
            self._logo_label = ctk.CTkLabel(
                self._sidebar,
                text="FFTESC Tool",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=COLORS['accent'],
            )
            self._logo_label.pack(pady=(10, 4))

        self._connection_panel = ConnectionPanel(self._sidebar, self._transport, fg_color='transparent')
        self._connection_panel.pack(fill='x')
        self._connection_panel.on_sim_data = self._on_simulator_data
        self._connection_panel.on_replay_data = self._on_simulator_data
        self._connection_panel.on_scan_request = self._scan_for_escs
        self._connection_panel.on_simulator_state_changed = self._on_simulator_state_changed
        self._discovered_escs: dict[int, FtescFirmwareInfo] = {}

        self._control_panel = ControlPanel(self._sidebar, self._transport, fg_color='transparent')
        self._control_panel.pack(fill='x')

        self._profile_panel = ProfilePanel(
            self._sidebar,
            on_collect_config=lambda: self._config_panel.collect_config_from_ui(),
            on_apply_config=lambda cfg: self._config_panel.apply_config_to_ui(cfg),
            fg_color='transparent'
        )
        self._profile_panel.pack(fill='x', pady=(8, 0))

        # Recovery button in sidebar
        self._recovery_button = ctk.CTkButton(
            self._sidebar,
            text="🆘 Réanimation",
            command=self._open_recovery_window,
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger_hover'],
            text_color=COLORS['text_primary'],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._recovery_button.pack(fill='x', pady=(10, 0), padx=10)

        theme_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=0, height=32)
        theme_frame.grid(row=1, column=0, sticky='ew')
        theme_frame.grid_propagate(False)
        ctk.CTkLabel(theme_frame, text="\U0001f319 Sombre", font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']).pack(side='left', padx=(15, 0))
        self._theme_var = ctk.BooleanVar(value=(ctk.get_appearance_mode() == "Light"))
        ctk.CTkSwitch(theme_frame, text="", variable=self._theme_var,
            command=self._toggle_theme, fg_color=COLORS['bg_light'],
            progress_color=COLORS['accent_blue'], button_hover_color=COLORS['accent'],
            switch_width=36, switch_height=18).pack(side='right', padx=(0, 15))
        ctk.CTkLabel(theme_frame, text="\u2600\ufe0f Clair", font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']).pack(side='right', padx=(0, 4))

        self._main_area = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'])
        self._main_area.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=10, pady=10)
        self._main_area.grid_rowconfigure(1, weight=1)
        self._main_area.grid_columnconfigure(0, weight=1)

        self._profile_frame = ctk.CTkFrame(self._main_area, fg_color=COLORS['bg_medium'], corner_radius=8)
        self._profile_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        ctk.CTkLabel(self._profile_frame, text="\U0001f4c1 Profile:", font=ctk.CTkFont(size=12, weight='bold'), text_color=COLORS['accent_blue']).pack(side='left', padx=(12, 5))
        self._profile_name_var = ctk.StringVar(value="")
        self._profile_name_entry = ctk.CTkEntry(self._profile_frame, textvariable=self._profile_name_var, width=150, font=ctk.CTkFont(size=12), fg_color=COLORS['bg_dark'], border_color=COLORS['accent_blue'])
        self._profile_name_entry.pack(side='left', padx=(0, 8))
        self._save_profile_btn = ctk.CTkButton(self._profile_frame, text="\U0001f4be Save", command=self._on_save_profile, fg_color=COLORS['accent_green'], hover_color=COLORS['success'], font=ctk.CTkFont(size=11), width=65, height=28)
        self._save_profile_btn.pack(side='left', padx=(0, 4))
        self._profile_list_var = ctk.StringVar(value="\U0001f4c2 Load...")
        self._profile_list_menu = ctk.CTkOptionMenu(self._profile_frame, variable=self._profile_list_var, values=["\U0001f4c2 Load..."], fg_color=COLORS['bg_dark'], button_color=COLORS['accent_blue'], font=ctk.CTkFont(size=11), width=120)
        self._profile_list_menu.pack(side='left', padx=(0, 4))
        self._load_profile_btn = ctk.CTkButton(self._profile_frame, text="Load", command=self._on_load_profile, fg_color=COLORS['accent_blue'], hover_color=COLORS['accent'], font=ctk.CTkFont(size=11), width=55, height=28)
        self._load_profile_btn.pack(side='left', padx=(0, 4))
        self._del_profile_btn = ctk.CTkButton(self._profile_frame, text="Del", command=self._on_delete_profile, fg_color=COLORS['danger'], hover_color='#b91c1c', font=ctk.CTkFont(size=11), width=45, height=28)
        self._del_profile_btn.pack(side='left', padx=(0, 4))
        self._refresh_profile_btn = ctk.CTkButton(self._profile_frame, text="\U0001f504", command=self._refresh_profile_list, fg_color=COLORS['bg_dark'], hover_color=COLORS['accent'], font=ctk.CTkFont(size=14), width=30, height=28)
        self._refresh_profile_btn.pack(side='left', padx=(0, 4))
        ctk.CTkButton(self._profile_frame, text="\U0001f4e4 Export", command=self._on_export_profile, fg_color=COLORS['bg_dark'], hover_color=COLORS['accent_blue'], font=ctk.CTkFont(size=10), width=55, height=28).pack(side='left', padx=(0, 4))
        ctk.CTkButton(self._profile_frame, text="\U0001f4e5 Import", command=self._on_import_profile, fg_color=COLORS['bg_dark'], hover_color=COLORS['accent_green'], font=ctk.CTkFont(size=10), width=55, height=28).pack(side='left', padx=(0, 4))
        self._refresh_profile_list()

        self._main_tabs = ctk.CTkTabview(self._main_area, fg_color=COLORS['bg_medium'], corner_radius=8)
        self._main_tabs.grid(row=1, column=0, sticky='nsew')

        self._main_tabs.add("T\u00e9l\u00e9m\u00e9trie")
        self._main_tabs.add("Configuration")
        self._main_tabs.add("🧙 Assistant")

        self._data_panel = RealtimeDataPanel(self._main_tabs.tab("T\u00e9l\u00e9m\u00e9trie"), fg_color=COLORS['bg_medium'], corner_radius=10)
        self._data_panel.pack(fill='both', expand=True)

        self._config_panel = ConfigPanel(self._main_tabs.tab("Configuration"), transport=self._transport, fg_color='transparent')
        self._config_panel.pack(fill='both', expand=True)

        self._wizard_panel = WizardPanel(
            self._main_tabs.tab("🧙 Assistant"),
            transport=self._transport,
            on_config_applied=self._on_wizard_applied,
            fg_color='transparent',
        )
        self._wizard_panel.pack(fill='both', expand=True)

        self._status_bar = StatusBar(self, fg_color=COLORS['bg_medium'], corner_radius=0)
        self._status_bar.grid(row=2, column=0, columnspan=2, sticky='ew')
        self._status_bar.add_donation_buttons()
        self._connection_panel.on_status_message = self._status_bar.show_message

        self._stats_timer()

        # Initialize recovery panel (hidden by default)
        self._recovery_panel = None

        # ── Icônes système (taskbar / dock / alt-tab) ─────────────────────────
        # update_idletasks() force la création de la fenêtre X11 avant wm_iconphoto
        self.update_idletasks()
        apply_window_icons(self)

    def _open_recovery_window(self):
        """Ouvre une fenêtre modale contenant le panneau de récupération."""
        if self._recovery_panel is not None and self._recovery_panel.winfo_exists():
            self._recovery_panel.focus()
            return

        # Create a new top-level window
        recovery_window = ctk.CTkToplevel(self)
        recovery_window.title("🆘 Zone de Récupération")
        recovery_window.geometry("400x500")
        recovery_window.resizable(False, False)

        # Make it modal
        recovery_window.transient(self)
        recovery_window.grab_set()

        # Create the recovery panel inside this window
        self._recovery_panel = RecoveryPanel(recovery_window, self._transport)
        self._recovery_panel.pack(fill='both', expand=True, padx=10, pady=10)

        # Handle window close
        def on_closing():
            self._recovery_panel = None
            recovery_window.destroy()

        recovery_window.protocol("WM_DELETE_WINDOW", on_closing)

    def _refresh_profile_list(self):
        profiles = list_profiles()
        values = ["\U0001f4c2 Load..."] + profiles if profiles else ["\U0001f4c2 Load..."]
        self._profile_list_menu.configure(values=values)
        if profiles:
            self._profile_list_var.set("\U0001f4c2 Load...")

    def _on_save_profile(self):
        name = self._profile_name_var.get().strip()
        if not name:
            tkmb.showwarning("Save Profile", "Please enter a profile name")
            return
        try:
            config = self._config_panel.collect_config_from_ui()
            errors = config.validate()
            has_errors = any(errors[k] for k in errors)
            if has_errors:
                all_errs = []
                for section, errs in errors.items():
                    if errs:
                        all_errs.append(f"  {section}: {'; '.join(errs)}")
                msg = "Validation errors:\n" + "\n".join(all_errs)
                if not tkmb.askyesno("Validation Warnings", msg + "\n\nSave anyway?"):
                    return
            config.name = name
            save_profile(name, config)
            self._profile_name_var.set(name)
            self._refresh_profile_list()
            tkmb.showinfo("Save Profile", f"Profile '{name}' saved successfully")
        except ValueError as e:
            tkmb.showerror("Error", f"Invalid value: {e}")
        except Exception as e:
            tkmb.showerror("Error", f"Failed to save: {e}")

    def _on_load_profile(self):
        name = self._profile_list_var.get()
        if name == "\U0001f4c2 Load..." or not name:
            tkmb.showinfo("Load Profile", "Select a profile from the dropdown first")
            return
        try:
            config = load_profile(name)
            if config is None:
                tkmb.showerror("Error", f"Profile '{name}' not found")
                return
            self._config_panel.apply_config_to_ui(config)
            self._profile_name_var.set(name)
            tkmb.showinfo("Load Profile", f"Profile '{name}' loaded")
        except Exception as e:
            tkmb.showerror("Error", f"Failed to load: {e}")

    def _on_delete_profile(self):
        name = self._profile_list_var.get()
        if name == "\U0001f4c2 Load..." or not name:
            tkmb.showinfo("Delete Profile", "Select a profile from the dropdown first")
            return
        if not tkmb.askyesno("Delete Profile", f"Delete profile '{name}'?"):
            return
        try:
            delete_profile(name)
            self._refresh_profile_list()
            self._profile_name_var.set("")
            tkmb.showinfo("Delete Profile", f"Profile '{name}' deleted")
        except Exception as e:
            tkmb.showerror("Error", f"Failed to delete: {e}")

    def _on_export_profile(self):
        name = self._profile_list_var.get()
        if name == "\U0001f4c2 Load..." or not name:
            tkmb.showinfo("Export Profile", "Select a profile from the dropdown first")
            return
        import tkinter.filedialog as filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{name}.json",
            title=f"Exporter le profil '{name}'"
        )
        if not path:
            return
        if export_profile(name, path):
            tkmb.showinfo("Export Profile", f"Profil '{name}' exporté vers {path}")
        else:
            tkmb.showerror("Export Error", f"Échec de l'export du profil '{name}'")

    def _on_import_profile(self):
        import tkinter.filedialog as filedialog
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importer un profil"
        )
        if not path:
            return
        config = import_profile(path)
        if config is None:
            tkmb.showerror("Import Error", "Fichier invalide ou corrompu")
            return
        self._config_panel.apply_config_to_ui(config)
        if config.name:
            self._profile_name_var.set(config.name)
        self._refresh_profile_list()
        tkmb.showinfo("Import Profile", f"Profil importé depuis {path}")

    def _set_logo_connected(self, connected: bool) -> None:
        """Swap logo sidebar entre état connecté (_on) et déconnecté."""
        update_connection_indicator(
            getattr(self, '_logo_label', None),
            connected,
            getattr(self, '_logo_images', {}),
        )

    def _on_simulator_state_changed(self, running: bool) -> None:
        """Bascule le logo connecté/déconnecté quand le simulateur démarre/s'arrête."""
        self._set_logo_connected(running)

    def _on_connection_changed(self, state: ConnectionState, message: str):
        self._connection_panel.update_state(state, message)
        self._status_bar.update_connection(state, message)
        if state == ConnectionState.CONNECTED:
            self._set_logo_connected(True)
            self._request_firmware()
        elif state in (ConnectionState.DISCONNECTED,
                       ConnectionState.ERROR,
                       ConnectionState.RECONNECTING):
            self._set_logo_connected(False)
            self._discovered_escs = {}
            self._connection_panel.show_discovered_escs({})

    def _request_firmware(self):
        transport = getattr(self, '_transport', None)
        if transport and transport.is_connected:
            self._discovered_escs = {}
            frame = build_obtain_all_ids_frame()
            transport.send(frame)
            self.after(800, self._process_scan_results)

    def _scan_for_escs(self):
        self._discovered_escs = {}
        transport = getattr(self, '_transport', None)
        if self._connection_panel._simulating:
            sim = self._connection_panel._sim_instance
            if sim:
                raw = build_frame(UartCommand.OBTAIN_ALL_FTESC_ID, b'')
                response = sim.handle_frame(raw)
                if response:
                    offset = 0
                    while offset < len(response):
                        cmd, payload, status = parse_frame(response[offset:])
                        if status != 'OK':
                            break
                        if cmd == UartCommand.OBTAIN_ALL_FTESC_ID:
                            fw = parse_firmware_info(payload)
                            if fw:
                                self._discovered_escs[fw.controller_id] = fw
                        header_byte = response[offset]
                        if header_byte == 0xAA:
                            frame_len = 2 + response[offset+1] + 2 + 1
                        elif header_byte == 0xBB:
                            frame_len = 3 + ((response[offset+1] << 8) | response[offset+2]) + 2 + 1
                        else:
                            break
                        offset += frame_len
        elif transport and transport.is_connected:
            frame = build_obtain_all_ids_frame()
            transport.send(frame)
        self.after(800, self._process_scan_results)

    def _process_scan_results(self):
        if self._connection_panel:
            self._connection_panel.show_discovered_escs(self._discovered_escs)
        for ctrl_id, fw_info in self._discovered_escs.items():
            motor_id = MOTOR_LABEL_A if ctrl_id == 0 else MOTOR_LABEL_B
            # update_motor_data en premier pour le controller_id label,
            # puis update_firmware_info pour le format riche (version + modèle)
            self._data_panel.update_motor_data(
                motor_id,
                FtescRealtimeData(controller_id=ctrl_id,
                                  firmware_version=fw_info.version_string))
            self._data_panel.update_firmware_info(motor_id, fw_info)

    def _on_raw_data(self, raw_data: bytes):
        """Dispatch chaque trame reçue. Supporte plusieurs trames concaténées."""
        offset = 0
        while offset < len(raw_data):
            try:
                command, payload, status = parse_frame(raw_data[offset:])
                if status != 'OK':
                    break
                self._dispatch_frame(command, payload)
                # Avancement : calcul de la longueur de la trame courante
                hdr = raw_data[offset]
                if hdr == 0xAA:
                    frame_len = 2 + raw_data[offset + 1] + 3   # hdr+len + payload+len + CRC(2) + footer(1)
                elif hdr == 0xBB:
                    frame_len = 3 + ((raw_data[offset + 1] << 8) | raw_data[offset + 2]) + 3
                else:
                    break
                offset += frame_len
            except Exception:
                break

    def _dispatch_frame(self, command: UartCommand, payload: bytes):
        """Traite une trame unique déjà décodée."""
        try:
            if command == UartCommand.OBTAIN_DATA_ONCE:
                rt_data = parse_realtime_data(payload)
                if rt_data:
                    self._last_data = rt_data
                    self.after(0, self._update_ui, rt_data)
            elif command == UartCommand.OBTAIN_FIRMWARE_VERSION:
                fw_info = parse_firmware_info(payload)
                if fw_info:
                    self.after(0, self._update_firmware_display, fw_info)
            elif command == UartCommand.READ_CONFIG:
                result = parse_config_response(payload)
                if result:
                    ctrl_id, sec_id, data = result
                    self.after(0, self._config_panel.on_config_read, ctrl_id, sec_id, data)
            elif command == UartCommand.WRITE_CONFIG:
                result = parse_config_response(payload)
                if result:
                    ctrl_id, sec_id, _ = result
                    sec_key = SECTION_NAMES.get(sec_id, "?")
                    print(f"[WRITE] Section {sec_key} confirmée (ctrl {ctrl_id})")
            elif command == UartCommand.OBTAIN_ALL_FTESC_ID:
                fw_info = parse_firmware_info(payload)
                if fw_info and getattr(self, '_discovered_escs', None) is not None:
                    self._discovered_escs[fw_info.controller_id] = fw_info
        except Exception as e:
            print(f"[DISPATCH] Erreur trame {command}: {e}")

    def _update_firmware_display(self, fw_info: FtescFirmwareInfo):
        motor_id = MOTOR_LABEL_A if fw_info.controller_id == 0 else MOTOR_LABEL_B
        self._data_panel.update_motor_data(
            motor_id, FtescRealtimeData(controller_id=fw_info.controller_id,
                                        firmware_version=fw_info.version_string))
        self._data_panel.update_firmware_info(motor_id, fw_info)
        # Mise à jour du panneau de connexion (ESC découvert via OBTAIN_FIRMWARE_VERSION)
        if getattr(self, '_discovered_escs', None) is not None:
            self._discovered_escs[fw_info.controller_id] = fw_info
            if self._connection_panel:
                self._connection_panel.show_discovered_escs(self._discovered_escs)

    def _on_error(self, message: str):
        print(f"[ERREUR] {message}")

    def _update_ui(self, data: FtescRealtimeData):
        self._data_panel.update_motor_data(MOTOR_LABEL_A, data)
        if hasattr(self._control_panel, 'log_data') and self._control_panel._logging:
            dual = FtescDualData(motor_a=data, motor_b=FtescRealtimeData(controller_id=1))
            self._control_panel.log_data(dual)

    def _on_simulator_data(self, dual_data):
        self.after(0, lambda: self._data_panel.update_motor_data(MOTOR_LABEL_A, dual_data.motor_a))
        self.after(0, lambda: self._data_panel.update_motor_data(MOTOR_LABEL_B, dual_data.motor_b))
        if hasattr(self._control_panel, 'log_data') and self._control_panel._logging:
            self._control_panel.log_data(dual_data)

    def _on_wizard_applied(self, dual_config):
        """Appelé par WizardPanel après application réussie.
        Synchronise la config dans le panneau Configuration."""
        if hasattr(self, '_config_panel'):
            try:
                self._config_panel.apply_config_to_ui(dual_config)
            except Exception:
                pass
        if hasattr(self, '_status_bar'):
            self._status_bar.show_message("🧙 Wizard : configuration appliquée")

    def _stats_timer(self):
        stats = self._transport.get_statistics()
        self._status_bar.update_stats(stats)
        self.after(1000, self._stats_timer)

    def _load_theme_config(self) -> str:
        try:
            with open(self._theme_config_path, 'r') as f:
                cfg = json.load(f)
            return "light" if cfg.get("theme") == "light" else "dark"
        except Exception:
            return "dark"

    def _save_theme_config(self, mode: str):
        try:
            with open(self._theme_config_path, 'w') as f:
                json.dump({"theme": mode}, f)
        except Exception:
            pass

    def _toggle_theme(self):
        mode = "light" if self._theme_var.get() else "dark"
        ctk.set_appearance_mode(mode)
        self._save_theme_config(mode)
        if hasattr(self, '_data_panel'):
            self._data_panel.refresh_theme()

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        if hasattr(self, '_control_panel') and self._control_panel:
            self._control_panel._auto_reading = False
            if hasattr(self._control_panel, '_current_var'): self._control_panel._current_var.set(0.0); self._control_panel._current_var = None
            if hasattr(self._control_panel, '_brake_var'): self._control_panel._brake_var.set(0.0); self._control_panel._brake_var = None
            if hasattr(self._control_panel, '_duty_var'): self._control_panel._duty_var.set(0.0); self._control_panel._duty_var = None
        self._transport.on_connection_changed = None
        self._transport.on_data_received = None
        self._transport.on_error = None
        if hasattr(self, '_connection_panel') and self._connection_panel:
            self._connection_panel._simulating = False
            if self._connection_panel._sim_instance:
                self._connection_panel._sim_instance.stop()
            self._connection_panel.destroy_monitor()
        self._transport.disconnect()
        super().destroy()


def main():
    app = FftescApp()
    app.mainloop()

if __name__ == '__main__':
    main()
