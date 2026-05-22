# -*- coding: utf-8 -*-
"""
gui/panels/recovery.py — Panneau de réanimation du contrôleur (Bootloader & ST-Link)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from gui.styles.colors import COLORS
from ftesc.transport import FtescTransport
from ftesc.protocol import UartCommand
import time


class RecoveryPanel(ctk.CTkFrame):
    def __init__(self, master, transport: FtescTransport, **kwargs):
        super().__init__(master, **kwargs)
        self.transport = transport

        self.configure(fg_color=COLORS['bg_light'], corner_radius=10)

        self._build_ui()

    def _build_ui(self):
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🆘 Zone de Récupération",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(pady=(15, 10), anchor='w', padx=15)

        # Separator
        separator = ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light'])
        separator.pack(fill='x', padx=15, pady=(0, 10))

        # --- Section 1: Diagnostic ---
        diag_frame = ctk.CTkFrame(self, fg_color="transparent")
        diag_frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(
            diag_frame,
            text="Diagnostic du MCU",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w')

        self.health_button = ctk.CTkButton(
            diag_frame,
            text="Vérifier l'état du MCU",
            command=self._check_mcu_health,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'],
            font=ctk.CTkFont(size=12)
        )
        self.health_button.pack(anchor='w', pady=(5, 0))

        self.health_label = ctk.CTkLabel(
            diag_frame,
            text="État inconnu",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        self.health_label.pack(anchor='w', pady=(2, 0))

        # Separator
        separator2 = ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light'])
        separator2.pack(fill='x', padx=15, pady=10)

        # --- Section 2: Mode Bootloader (UART) ---
        boot_frame = ctk.CTkFrame(self, fg_color="transparent")
        boot_frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(
            boot_frame,
            text="Mode Bootloader (UART)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w')

        self.boot_button = ctk.CTkButton(
            boot_frame,
            text="Forcer le mode Bootloader",
            command=self._enter_bootloader,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'],
            font=ctk.CTkFont(size=12)
        )
        self.boot_button.pack(anchor='w', pady=(5, 0))

        warning_label = ctk.CTkLabel(
            boot_frame,
            text="⚠️ Le contrôleur redémarrera en mode flash. Assurez-vous d'avoir le fichier .bin prêt.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['warning'],
            wraplength=300,
            justify="left"
        )
        warning_label.pack(anchor='w', pady=(2, 0))

        # Separator
        separator3 = ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light'])
        separator3.pack(fill='x', padx=15, pady=10)

        # --- Section 3: Mode ST-Link (Physique) ---
        stlink_frame = ctk.CTkFrame(self, fg_color="transparent")
        stlink_frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(
            stlink_frame,
            text="Mode ST-Link (Physique)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w')

        self.stlink_button = ctk.CTkButton(
            stlink_frame,
            text="Voir le guide de câblage",
            command=self._show_stlink_guide,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'],
            font=ctk.CTkFont(size=12)
        )
        self.stlink_button.pack(anchor='w', pady=(5, 0))

        # Simple text schematic
        schematic_label = ctk.CTkLabel(
            stlink_frame,
            text=(
                "Schéma de câblage ST-Link V2/V3 :\n"
                "  SWDIO  → PA13\n"
                "  SWCLK  → PA14\n"
                "  GND    → GND\n"
                "  3.3V   → 3.3V\n"
                "  NRST   → NRST (optionnel pour reset)"
            ),
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary'],
            justify="left"
        )
        schematic_label.pack(anchor='w', pady=(2, 0))

        # Link to STM32CubeProgrammer
        link_label = ctk.CTkLabel(
            stlink_frame,
            text="🔗 Télécharger STM32CubeProgrammer (STMicroelectronics)",
            font=ctk.CTkFont(size=11, underline=True),
            text_color=COLORS['accent_blue'],
            cursor="hand2"
        )
        link_label.pack(anchor='w', pady=(5, 0))
        link_label.bind("<Button-1>", lambda e: self._open_stlink_url())

        # Warning
        warn_label = ctk.CTkLabel(
            stlink_frame,
            text="⚠️ Cette opération annule la garantie et peut brick le dispositif si mal effectuée.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['danger'],
            wraplength=300,
            justify="left"
        )
        warn_label.pack(anchor='w', pady=(2, 0))

    def _check_mcu_health(self):
        """Vérifie l'état du MCU et met à jour le label."""
        self.health_button.configure(state="disabled")
        self.health_label.configure(text="Vérification...", text_color=COLORS['text_secondary'])
        self.update_idletasks()

        try:
            health = self.transport.check_mcu_health()
            if health == "Sain":
                self.health_label.configure(text="MCU Sain", text_color=COLORS['success'])
            elif health == "Corrompu":
                self.health_label.configure(text="MCU Corrompu", text_color=COLORS['danger'])
            elif health == "Inconnu":
                self.health_label.configure(text="État Inconnu", text_color=COLORS['warning'])
            else:
                self.health_label.configure(text=health, text_color=COLORS['danger'])
        except Exception as e:
            self.health_label.configure(text=f"Erreur : {e}", text_color=COLORS['danger'])
        finally:
            self.health_button.configure(state="normal")

    def _enter_bootloader(self):
        """Demande confirmation puis force le MCU en mode bootloader."""
        result = messagebox.askyesno(
            "Confirmation",
            "Êtes-vous sûr de vouloir forcer le redémarrage en mode bootloader ?\n"
            "Le contrôleur sera déconnecté et redémarrera.",
            icon='warning'
        )
        if result:
            try:
                self.transport.enter_bootloader()
                # Show info that the device is rebooting
                messagebox.showinfo(
                    "Redémarrage",
                    "Le contrôleur redémarre en mode bootloader.\n"
                    "Vous pouvez maintenant flasher le firmware avec votre outil préféré."
                )
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible d'entrer en mode bootloader : {e}"
                )

    def _show_stlink_guide(self):
        """Affiche une fenêtre avec le guide de câblage ST-Link."""
        guide_window = ctk.CTkToplevel(self)
        guide_window.title("Guide de câblage ST-Link")
        guide_window.geometry("350x250")
        guide_window.resizable(False, False)

        # Make it modal
        guide_window.transient(self.master)
        guide_window.grab_set()

        # Content
        frame = ctk.CTkFrame(guide_window, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Guide de câblage ST-Link V2/V3",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 10))

        schematic_text = (
            "Connections nécessaires :\n\n"
            "  ST-Link     →  FTESC\n"
            "  ----------------------\n"
            "  SWDIO  →  PA13\n"
            "  SWCLK  →  PA14\n"
            "  GND    →  GND\n"
            "  3.3V   →  3.3V\n"
            "  NRST   →  NRST (optionnel)\n\n"
            "Assurez-vous que l'alimentation du FTESC est coupée\n"
            "avant de connecter le 3.3V du ST-Link."
        )

        ctk.CTkLabel(
            frame,
            text=schematic_text,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary'],
            justify="left"
        ).pack(anchor='w', pady=(0, 10))

        # Close button
        close_btn = ctk.CTkButton(
            frame,
            text="Fermer",
            command=guide_window.destroy,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary']
        )
        close_btn.pack(anchor='e', pady=(10, 0))

    def _open_stlink_url(self):
        """Ouvre le navigateur vers la page de téléchargement de STM32CubeProgrammer."""
        import webbrowser
        webbrowser.open("https://www.st.com/en/development-tools/stm32cubeprog.html")