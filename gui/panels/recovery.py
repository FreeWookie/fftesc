# -*- coding: utf-8 -*-
"""
gui/panels/recovery.py — Panneau de réanimation du contrôleur (Bootloader, ST-Link, ID)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from gui.styles.colors import COLORS
from ftesc.transport import FtescTransport
from ftesc.protocol import UartCommand


class RecoveryPanel(ctk.CTkFrame):
    def __init__(self, master, transport: FtescTransport, **kwargs):
        super().__init__(master, **kwargs)
        self.transport = transport

        self.configure(fg_color=COLORS['bg_light'], corner_radius=10)

        self._discovered_ids: list[int] = []
        self._id_widgets: dict[int, dict] = {}

        self._build_ui()

    def _build_ui(self):
        title_label = ctk.CTkLabel(
            self,
            text="\U0001f6a8 Zone de Récupération",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(pady=(15, 10), anchor='w', padx=15)

        separator = ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light'])
        separator.pack(fill='x', padx=15, pady=(0, 10))

        self._build_diagnostic_section()
        self._build_bootloader_section()
        self._build_esc_id_section()
        self._build_stlink_section()

    def _make_section_title(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w')

    def _make_separator(self):
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light'])
        sep.pack(fill='x', padx=15, pady=10)
        return sep

    # ── Section 1: Diagnostic ─────────────────────────────────

    def _build_diagnostic_section(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill='x', padx=15, pady=5)

        self._make_section_title(frame, "Diagnostic du MCU")

        self.health_button = ctk.CTkButton(
            frame, text="Vérifier l'état du MCU",
            command=self._check_mcu_health,
            fg_color=COLORS['bg_light'], hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'], font=ctk.CTkFont(size=12)
        )
        self.health_button.pack(anchor='w', pady=(5, 0))

        self.health_label = ctk.CTkLabel(
            frame, text="État inconnu",
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']
        )
        self.health_label.pack(anchor='w', pady=(2, 0))

    # ── Section 2: Bootloader ─────────────────────────────────

    def _build_bootloader_section(self):
        self._make_separator()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill='x', padx=15, pady=5)

        self._make_section_title(frame, "Mode Bootloader (UART)")

        self.boot_button = ctk.CTkButton(
            frame, text="Forcer le mode Bootloader",
            command=self._enter_bootloader,
            fg_color=COLORS['bg_light'], hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'], font=ctk.CTkFont(size=12)
        )
        self.boot_button.pack(anchor='w', pady=(5, 0))

        ctk.CTkLabel(
            frame,
            text="\u26a0\ufe0f Le contrôleur redémarrera en mode flash. Assurez-vous d'avoir le fichier .bin prêt.",
            font=ctk.CTkFont(size=11), text_color=COLORS['warning'],
            wraplength=300, justify="left"
        ).pack(anchor='w', pady=(2, 0))

    # ── Section 3: ESC ID Reassignment ────────────────────────

    def _build_esc_id_section(self):
        self._make_separator()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill='x', padx=15, pady=5)

        self._make_section_title(frame, "Réaffectation des ID ESC")

        desc = ctk.CTkLabel(
            frame,
            text="Permet de changer l'ID d'un ESC. Utile en configuration double "
                 "quand un ESC est bloqué (briqué) :\n"
                 "  • 🔍 Découvrir → liste les ESC sur le bus\n"
                 "  • Saisir le nouvel ID → Appliquer\n"
                 "  • 💾 Sauvegarder en EEPROM → pour rendre permanent\n\n"
                 "Si SET_ID_CURRENT n'est pas supporté par le firmware :\n"
                 "utilisez le mode Bootloader + STM32CubeProgrammer "
                 "pour reflasher l'ESC avec l'ID souhaité.",
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
            wraplength=320, justify="left"
        )
        desc.pack(anchor='w', pady=(5, 8))

        # Discover button
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill='x', pady=(0, 5))

        self.discover_btn = ctk.CTkButton(
            btn_row, text="🔍 Découvrir les ESC",
            command=self._discover_escs,
            fg_color=COLORS['accent_blue'], hover_color=COLORS['mauve_hover'],
            text_color='white', font=ctk.CTkFont(size=12)
        )
        self.discover_btn.pack(side='left', padx=(0, 8))

        self.id_status_label = ctk.CTkLabel(
            btn_row, text="",
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary']
        )
        self.id_status_label.pack(side='left')

        # Container for discovered ESC cards
        self._id_cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._id_cards_frame.pack(fill='x')

        # Save to EEPROM button (hidden until IDs are set)
        self.save_eeprom_btn = ctk.CTkButton(
            frame, text="💾 Sauvegarder en EEPROM",
            command=self._save_eeprom,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_green'],
            text_color=COLORS['text_primary'], font=ctk.CTkFont(size=12)
        )
        # Don't pack yet - only show after successful ID set

    def _discover_escs(self):
        self.discover_btn.configure(state='disabled', text='🔍 Recherche...')
        self.id_status_label.configure(text='')
        # Clear old cards
        for w in self._id_cards_frame.winfo_children():
            w.destroy()
        self._id_widgets.clear()
        threading.Thread(target=self._discover_thread, daemon=True).start()

    def _discover_thread(self):
        try:
            ids = self.transport.obtain_all_ids(timeout=2.0)
            self.after(0, self._on_discovered, ids)
        except Exception as e:
            self.after(0, self.id_status_label.configure,
                       text=f"Erreur: {e}", text_color=COLORS['danger'])
            self.after(0, self.discover_btn.configure,
                       state='normal', text='🔍 Découvrir les ESC')

    def _on_discovered(self, ids: list[int]):
        self.discover_btn.configure(state='normal', text='🔍 Découvrir les ESC')
        if not ids:
            self.id_status_label.configure(
                text="Aucun ESC détecté", text_color=COLORS['warning'])
            return
        self._discovered_ids = ids
        self.id_status_label.configure(
            text=f"{len(ids)} ESC trouvé(s): {', '.join(map(str, ids))}",
            text_color=COLORS['success'])

        for cid in ids:
            card = ctk.CTkFrame(self._id_cards_frame, fg_color=COLORS['bg_medium'],
                                corner_radius=6)
            card.pack(fill='x', pady=3)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill='x', padx=8, pady=6)

            ctk.CTkLabel(
                row, text=f"ESC ID actuel: {cid}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['text_primary']
            ).pack(side='left', padx=(0, 10))

            ctk.CTkLabel(row, text="→ Nouvel ID:",
                         font=ctk.CTkFont(size=12),
                         text_color=COLORS['text_secondary']).pack(side='left')

            id_var = ctk.StringVar(value=str(cid))
            id_entry = ctk.CTkEntry(row, textvariable=id_var, width=50,
                                     font=ctk.CTkFont(size=12),
                                     fg_color=COLORS['bg_dark'],
                                     border_color=COLORS['accent_blue'])
            id_entry.pack(side='left', padx=(4, 8))

            set_btn = ctk.CTkButton(
                row, text="Appliquer",
                command=lambda c=cid, v=id_var: self._set_esc_id(c, v),
                fg_color=COLORS['accent_blue'], hover_color=COLORS['mauve_hover'],
                text_color='white', font=ctk.CTkFont(size=11), width=80, height=28
            )
            set_btn.pack(side='left')

            status_lbl = ctk.CTkLabel(
                row, text="", font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            )
            status_lbl.pack(side='left', padx=(8, 0))

            self._id_widgets[cid] = {
                'var': id_var, 'entry': id_entry,
                'btn': set_btn, 'status': status_lbl, 'card': card
            }

    def _set_esc_id(self, current_id: int, var: ctk.StringVar):
        try:
            new_id = int(var.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "L'ID doit être un nombre entier (0-255)")
            return
        if new_id < 0 or new_id > 255:
            messagebox.showerror("Erreur", "L'ID doit être compris entre 0 et 255")
            return

        w = self._id_widgets.get(current_id)
        if w:
            w['btn'].configure(state='disabled', text='⏳')
            w['status'].configure(text="", text_color=COLORS['text_secondary'])

        threading.Thread(
            target=self._set_id_thread,
            args=(current_id, new_id),
            daemon=True
        ).start()

    def _set_id_thread(self, current_id: int, new_id: int):
        try:
            success = self.transport.set_esc_id(new_id, current_ma=0, timeout=2.0)
            self.after(0, self._on_id_set, current_id, new_id, success)
        except Exception as e:
            self.after(0, self._on_id_set, current_id, new_id, False, str(e))

    def _on_id_set(self, current_id: int, new_id: int, success: bool, error: str = ""):
        w = self._id_widgets.get(current_id)
        if w:
            w['btn'].configure(state='normal', text='Appliquer')
            if success:
                w['status'].configure(text=f"✓ ID changé → {new_id}",
                                      text_color=COLORS['success'])
                # Update the card header with new ID
                self.id_status_label.configure(
                    text="ID changé avec succès. Sauvegardez en EEPROM !",
                    text_color=COLORS['success'])
                self.save_eeprom_btn.pack(anchor='w', pady=(8, 0))
            else:
                err = error or "Pas de réponse"
                w['status'].configure(text=f"✗ Échec: {err}",
                                      text_color=COLORS['danger'])

    def _save_eeprom(self):
        if not messagebox.askyesno(
                "Sauvegarde EEPROM",
                "Confirmer la sauvegarde des nouveaux ID en EEPROM ?\n"
                "Le contrôleur va redémarrer après la sauvegarde.",
                icon='warning'):
            return
        self.save_eeprom_btn.configure(state='disabled', text='💾 Sauvegarde...')
        threading.Thread(target=self._save_eeprom_thread, daemon=True).start()

    def _save_eeprom_thread(self):
        try:
            from ftesc.protocol import build_frame
            frame = build_frame(UartCommand.SAVE_EEPROM, b'')
            self.transport.send(frame)
            time.sleep(0.5)
            self.after(0, lambda: messagebox.showinfo(
                "EEPROM", "ID sauvegardés. Redémarrez le contrôleur pour appliquer."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        finally:
            self.after(0, lambda: self.save_eeprom_btn.configure(
                state='normal', text='💾 Sauvegarder en EEPROM'))

    # ── Section 4: ST-Link ────────────────────────────────────

    def _build_stlink_section(self):
        self._make_separator()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill='x', padx=15, pady=5)

        self._make_section_title(frame, "Mode ST-Link (Physique)")

        self.stlink_button = ctk.CTkButton(
            frame, text="Voir le guide de câblage",
            command=self._show_stlink_guide,
            fg_color=COLORS['bg_light'], hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary'], font=ctk.CTkFont(size=12)
        )
        self.stlink_button.pack(anchor='w', pady=(5, 0))

        ctk.CTkLabel(
            frame,
            text=("Schéma de câblage ST-Link V2/V3 :\n"
                  "  SWDIO  → PA13\n"
                  "  SWCLK  → PA14\n"
                  "  GND    → GND\n"
                  "  3.3V   → 3.3V\n"
                  "  NRST   → NRST (optionnel pour reset)"),
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
            justify="left"
        ).pack(anchor='w', pady=(2, 0))

        link_label = ctk.CTkLabel(
            frame,
            text="🔗 Télécharger STM32CubeProgrammer (STMicroelectronics)",
            font=ctk.CTkFont(size=11, underline=True),
            text_color=COLORS['accent_blue'], cursor="hand2"
        )
        link_label.pack(anchor='w', pady=(5, 0))
        link_label.bind("<Button-1>", lambda e: self._open_stlink_url())

        ctk.CTkLabel(
            frame,
            text="\u26a0\ufe0f Cette opération annule la garantie et peut brick le dispositif si mal effectuée.",
            font=ctk.CTkFont(size=10), text_color=COLORS['danger'],
            wraplength=300, justify="left"
        ).pack(anchor='w', pady=(2, 0))

    def _check_mcu_health(self):
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
        result = messagebox.askyesno(
            "Confirmation",
            "Êtes-vous sûr de vouloir forcer le redémarrage en mode bootloader ?\n"
            "Le contrôleur sera déconnecté et redémarrera.",
            icon='warning'
        )
        if result:
            try:
                self.transport.enter_bootloader()
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
        guide_window = ctk.CTkToplevel(self)
        guide_window.title("Guide de câblage ST-Link")
        guide_window.geometry("350x250")
        guide_window.resizable(False, False)
        guide_window.transient(self.master)
        guide_window.grab_set()

        frame = ctk.CTkFrame(guide_window, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Guide de câblage ST-Link V2/V3",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text=("Connections nécessaires :\n\n"
                  "  ST-Link     →  FTESC\n"
                  "  ----------------------\n"
                  "  SWDIO  →  PA13\n"
                  "  SWCLK  →  PA14\n"
                  "  GND    →  GND\n"
                  "  3.3V   →  3.3V\n"
                  "  NRST   →  NRST (optionnel)\n\n"
                  "Assurez-vous que l'alimentation du FTESC est coupée\n"
                  "avant de connecter le 3.3V du ST-Link."),
            font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary'],
            justify="left"
        ).pack(anchor='w', pady=(0, 10))

        ctk.CTkButton(
            frame, text="Fermer", command=guide_window.destroy,
            fg_color=COLORS['bg_light'], hover_color=COLORS['mauve_hover'],
            text_color=COLORS['text_primary']
        ).pack(anchor='e', pady=(10, 0))

    def _open_stlink_url(self):
        import webbrowser
        webbrowser.open("https://www.st.com/en/development-tools/stm32cubeprog.html")
