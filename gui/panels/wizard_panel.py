# -*- coding: utf-8 -*-
"""
gui/panels/wizard_panel.py — Assistant de configuration FTESC (Wizard 5 étapes).

Workflow :
    Étape 1 : Niveau d'expérience  (Débutant / Avancé / Expert)
    Étape 2 : Moteur & Transmission (modèle, KV, transmission, ratio, roue)
    Étape 3 : Batterie              (modèle, capacité optionnelle)
    Étape 4 : Résumé & Validation   (résultats calculés + bouton Appliquer)
    Étape 5 : Application           (barre de progression + feedback)
"""
from __future__ import annotations

import threading
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as tkmb
from typing import Optional, Callable

import customtkinter as ctk

from ftesc import FtescTransport
from ftesc.config_protocol import (
    SEC_MOTOR, SEC_LIMITS, SEC_RAMP, SEC_BATTERY,
    build_write_config_frame,
)
from ftesc.profiles import save_profile
from ftesc.wizard_engine import WizardEngine, WizardInputs, WizardResult
from gui.styles.colors import COLORS
from gui.i18n import _
from gui.wizard_data import (
    motor_names, battery_names, transmission_names, PROFILES,
)

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers internes
# ──────────────────────────────────────────────────────────────────────────────

def _section_label(parent, text: str, **kw) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=COLORS['text_secondary'], **kw)


def _field_label(parent, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=12),
        text_color=COLORS['text_secondary'], anchor='w')


def _result_row(parent, label: str, value: str, unit: str, row: int, accent=None):
    """Ligne label / valeur / unité dans la grille résumé."""
    accent = accent or COLORS['text_primary']
    ctk.CTkLabel(parent, text=label,
                 font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary'],
                 anchor='w').grid(row=row, column=0, sticky='w', padx=(0, 12), pady=3)
    ctk.CTkLabel(parent, text=value,
                 font=ctk.CTkFont(size=13, weight='bold'), text_color=accent,
                 anchor='e').grid(row=row, column=1, sticky='e', pady=3)
    ctk.CTkLabel(parent, text=unit,
                 font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
                 anchor='w').grid(row=row, column=2, sticky='w', padx=(4, 0), pady=3)


# ──────────────────────────────────────────────────────────────────────────────
#  WizardPanel
# ──────────────────────────────────────────────────────────────────────────────

class WizardPanel(ctk.CTkFrame):
    """
    Panneau principal du wizard.

    Paramètres
    ----------
    parent      : widget parent CTk
    transport   : FtescTransport partagé avec le reste de l'application
    on_config_applied : callback(DualMotorConfig) — appelé après application réussie
    """

    _TOTAL_STEPS = 4    # étapes visibles (l'étape 5 « application » est inline)

    def __init__(
        self,
        parent,
        transport: FtescTransport,
        on_config_applied: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._transport       = transport
        self._on_applied      = on_config_applied
        self._engine          = WizardEngine()
        self._result: Optional[WizardResult] = None
        self._current_step    = 1
        self._applying        = False

        self.configure(fg_color=COLORS['bg_dark'])
        self._build_chrome()
        self._show_step(1)

    # ── Chrome (en-tête + navigation + zone contenu) ──────────────────────────

    def _build_chrome(self):
        # ── En-tête ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=8)
        header.pack(fill='x', padx=16, pady=(14, 0))

        ctk.CTkLabel(header, text=_("wizard.title"),
                     font=ctk.CTkFont(size=17, weight='bold'),
                     text_color=COLORS['mauve']).pack(side='left', padx=14, pady=10)

        self._step_indicator = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'])
        self._step_indicator.pack(side='right', padx=14)

        ctk.CTkLabel(self, text=_("wizard.subtitle"),
                     font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']
                     ).pack(padx=16, pady=(6, 0), anchor='w')

        # ── Barre de progression par étapes ──────────────────────────────────
        prog_row = ctk.CTkFrame(self, fg_color='transparent')
        prog_row.pack(fill='x', padx=16, pady=(8, 0))
        self._step_bars: list[ctk.CTkProgressBar] = []
        for i in range(self._TOTAL_STEPS):
            bar = ctk.CTkProgressBar(prog_row, height=5, corner_radius=3,
                                     progress_color=COLORS['mauve'],
                                     fg_color=COLORS['bg_light'])
            bar.set(0)
            bar.pack(side='left', fill='x', expand=True, padx=(0 if i == 0 else 3, 0))
            self._step_bars.append(bar)

        # ── Séparateur ───────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=COLORS['bg_light']
                     ).pack(fill='x', padx=16, pady=(10, 0))

        # ── Zone de contenu (défilable) ───────────────────────────────────────
        self._content_outer = ctk.CTkFrame(self, fg_color='transparent')
        self._content_outer.pack(fill='both', expand=True, padx=16, pady=8)

        self._content_scroll = ctk.CTkScrollableFrame(
            self._content_outer, fg_color=COLORS['bg_medium'], corner_radius=8)
        self._content_scroll.pack(fill='both', expand=True)

        # ── Barre d'état wizard ───────────────────────────────────────────────
        self._status_var = ctk.StringVar(value="")
        self._status_lbl = ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
            wraplength=650, justify='left')
        self._status_lbl.pack(padx=16, pady=(0, 4), anchor='w')

        # ── Barre de progression application ─────────────────────────────────
        self._apply_progress = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            progress_color=COLORS['accent_green'], fg_color=COLORS['bg_light'])
        # cachée par défaut

        # ── Navigation ───────────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=0, height=48)
        nav.pack(fill='x', side='bottom')
        nav.pack_propagate(False)

        self._btn_back = ctk.CTkButton(
            nav, text=_("wizard.nav.back"),
            command=self._go_back,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=12), width=110, height=32)
        self._btn_back.pack(side='left', padx=12, pady=8)

        self._btn_next = ctk.CTkButton(
            nav, text=_("wizard.nav.next"),
            command=self._go_next,
            fg_color=COLORS['mauve'], hover_color=COLORS['mauve_hover'],
            font=ctk.CTkFont(size=12, weight='bold'), width=130, height=32)
        self._btn_next.pack(side='right', padx=12, pady=8)

    # ── Contrôle de navigation ────────────────────────────────────────────────

    def _go_next(self):
        if self._applying:
            return
        if self._current_step < self._TOTAL_STEPS:
            if not self._validate_current_step():
                return
            self._show_step(self._current_step + 1)
        elif self._current_step == self._TOTAL_STEPS:
            # Étape 4 → bouton "Appliquer" géré directement dans l'étape
            pass

    def _go_back(self):
        if self._applying:
            return
        if self._current_step > 1:
            self._show_step(self._current_step - 1)

    def _show_step(self, step: int):
        self._current_step = step
        self._clear_content()
        self._update_nav_buttons()
        self._update_step_bars()
        self._status_var.set("")

        builders = {
            1: self._build_step1,
            2: self._build_step2,
            3: self._build_step3,
            4: self._build_step4,
        }
        builders.get(step, lambda: None)()

    def _clear_content(self):
        for w in self._content_scroll.winfo_children():
            w.destroy()

    def _update_nav_buttons(self):
        s = self._current_step
        self._btn_back.configure(state='normal' if s > 1 else 'disabled')
        if s < self._TOTAL_STEPS:
            self._btn_next.configure(
                text=_("wizard.nav.next") if s < 3 else _("wizard.nav.calculate"),
                state='normal')
        else:
            # Étape 4 : le bouton next disparaît (remplacé par le bouton Apply inline)
            self._btn_next.configure(state='disabled', text="")

    def _update_step_bars(self):
        for i, bar in enumerate(self._step_bars):
            bar.set(1.0 if i < self._current_step else 0.0)
        self._step_indicator.configure(
            text=f"Étape {self._current_step} / {self._TOTAL_STEPS}")

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_current_step(self) -> bool:
        """Valide les champs de l'étape courante. Retourne False si invalide."""
        if self._current_step == 1:
            if not hasattr(self, '_profile_var') or not self._profile_var.get():
                self._set_status(_("wizard.error.invalid_fields"), error=True)
                return False
        elif self._current_step == 2:
            if not self._validate_step2():
                return False
        elif self._current_step == 3:
            # Étape 3 : lancement du calcul
            return self._run_calculation()
        return True

    def _validate_step2(self) -> bool:
        # KV
        kv_txt = self._kv_var.get().strip()
        if kv_txt:
            try:
                kv = float(kv_txt)
                if not (1 <= kv <= 10000):
                    raise ValueError
            except ValueError:
                self._set_status("KV doit être entre 1 et 10 000", error=True)
                return False

        # Pignon moteur (optionnel)
        p_txt = self._pinion_var.get().strip()
        if p_txt:
            try:
                p = int(p_txt)
                if not (10 <= p <= 30):
                    raise ValueError
            except ValueError:
                self._set_status("Dents pignon : entier entre 10 et 30", error=True)
                return False

        # Poulie roue (optionnel, mais requis si pignon renseigné)
        w_txt = self._wheel_teeth_var.get().strip()
        if w_txt:
            try:
                w = int(w_txt)
                if not (40 <= w <= 120):
                    raise ValueError
            except ValueError:
                self._set_status("Dents poulie roue : entier entre 40 et 120", error=True)
                return False
        if p_txt and not w_txt:
            self._set_status("Renseignez aussi les dents de la poulie roue", error=True)
            return False
        if w_txt and not p_txt:
            self._set_status("Renseignez aussi les dents du pignon moteur", error=True)
            return False

        # Ratio manuel (uniquement si pas de pignon/poulie)
        if not p_txt and not w_txt:
            ratio_txt = self._ratio_var.get().strip()
            try:
                ratio = float(ratio_txt)
                if ratio <= 0:
                    raise ValueError
            except ValueError:
                self._set_status("Rapport de réduction invalide (> 0)", error=True)
                return False

        # Diamètre roue (optionnel)
        diam_txt = self._wheel_var.get().strip()
        if diam_txt:
            try:
                d = float(diam_txt)
                if d <= 0:
                    raise ValueError
            except ValueError:
                self._set_status("Diamètre de roue invalide (> 0)", error=True)
                return False

        # Efficacité
        try:
            eff = self._efficiency_var.get()
            if not (0.70 <= eff <= 0.95):
                raise ValueError
        except (ValueError, Exception):
            self._set_status("Efficacité doit être entre 70% et 95%", error=True)
            return False

        return True

    def _run_calculation(self) -> bool:
        """
        Construit WizardInputs, lance le calcul, stocke le résultat.

        Fallback garanti : si le calcul échoue, self._result garde sa valeur
        précédente — l'interface standard n'est jamais modifiée.
        """
        try:
            kv_txt   = self._kv_var.get().strip()
            kv       = float(kv_txt) if kv_txt else None
            ratio    = float(self._ratio_var.get().strip())
            wheel_txt = self._wheel_var.get().strip()
            wheel    = float(wheel_txt) if wheel_txt else None
            cap_txt  = self._cap_var.get().strip()

            # Pignon / poulie (optionnels)
            p_txt = self._pinion_var.get().strip()
            wt_txt = self._wheel_teeth_var.get().strip()
            pinion = int(p_txt) if p_txt else None
            wheel_teeth = int(wt_txt) if wt_txt else None

            inputs = WizardInputs(
                motor_model             = self._motor_var.get(),
                battery_name            = self._battery_var.get(),
                transmission            = self._trans_var.get(),
                gear_ratio              = ratio,
                wheel_mm                = wheel,
                profile                 = self._profile_var.get(),
                dual_motor              = True,
                config_name             = f"Wizard — {self._profile_var.get()}",
                kv_override             = kv,
                pinion_teeth            = pinion,
                wheel_teeth             = wheel_teeth,
                wheel_unit              = self._wheel_unit_var.get(),
                speed_unit              = self._speed_unit_var.get(),
                transmission_efficiency = self._efficiency_var.get(),
            )
            # Calcul dans une variable temporaire : on n'écrase _result
            # qu'en cas de succès total (garantie de fallback)
            pending = self._engine.calculate_config(inputs)

            # Stocke la capacité (non gérée par le moteur — usage futur autonomie)
            if cap_txt:
                try:
                    pending.config.battery.capacity = float(cap_txt)
                except ValueError:
                    pass

            # ✅ Succès : on valide le résultat
            self._result = pending
            return True
        except ValueError as e:
            self._set_status(_("wizard.error.calculation").format(e=e), error=True)
            return False
        except Exception as e:
            self._set_status(_("wizard.error.calculation").format(e=e), error=True)
            return False

    # ── Étape 1 — Niveau ──────────────────────────────────────────────────────

    def _build_step1(self):
        s = self._content_scroll
        _section_label(s, _("wizard.step1.title")).pack(padx=14, pady=(14, 4), anchor='w')
        ctk.CTkLabel(s, text=_("wizard.step1.question"),
                     font=ctk.CTkFont(size=14, weight='bold'),
                     text_color=COLORS['text_primary']).pack(padx=14, pady=(0, 16))

        if not hasattr(self, '_profile_var'):
            self._profile_var = ctk.StringVar(value="Avancé")

        profiles_data = [
            ("Débutant", _("wizard.step1.beginner"),
             _("wizard.step1.beginner_desc"), COLORS['accent_green']),
            ("Avancé",   _("wizard.step1.advanced"),
             _("wizard.step1.advanced_desc"),   COLORS['accent_blue']),
            ("Expert",   _("wizard.step1.expert"),
             _("wizard.step1.expert_desc"),  COLORS['accent']),
        ]
        for profile_key, label, desc, color in profiles_data:
            self._build_profile_card(s, profile_key, label, desc, color)

    def _build_profile_card(self, parent, key: str, label: str, desc: str, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_light'], corner_radius=8)
        card.pack(fill='x', padx=14, pady=5)

        rb = ctk.CTkRadioButton(
            card, text=label, variable=self._profile_var, value=key,
            font=ctk.CTkFont(size=13, weight='bold'), text_color=color,
            fg_color=color, hover_color=color)
        rb.pack(side='left', padx=14, pady=10)

        ctk.CTkLabel(
            card, text=desc,
            font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary'],
            anchor='w').pack(side='left', padx=(0, 14), pady=10, fill='x', expand=True)

        # Sélection au clic sur la carte entière
        card.bind("<Button-1>", lambda e, k=key: self._profile_var.set(k))

    # ── Étape 2 — Moteur ──────────────────────────────────────────────────────

    def _build_step2(self):
        s = self._content_scroll
        _section_label(s, _("wizard.step2.title")).pack(padx=14, pady=(14, 10), anchor='w')

        if not hasattr(self, '_motor_var'):
            self._motor_var = ctk.StringVar(value=motor_names()[0])
        if not hasattr(self, '_kv_var'):
            self._kv_var = ctk.StringVar(value="")
        if not hasattr(self, '_trans_var'):
            self._trans_var = ctk.StringVar(value=transmission_names()[0])
        if not hasattr(self, '_ratio_var'):
            self._ratio_var = ctk.StringVar(value="1.0")
        if not hasattr(self, '_wheel_var'):
            self._wheel_var = ctk.StringVar(value="")
        # ── Nouveaux champs D30 ──────────────────────────────────────────────
        if not hasattr(self, '_pinion_var'):
            self._pinion_var = ctk.StringVar(value="")
        if not hasattr(self, '_wheel_teeth_var'):
            self._wheel_teeth_var = ctk.StringVar(value="")
        if not hasattr(self, '_wheel_unit_var'):
            self._wheel_unit_var = ctk.StringVar(value="mm")
        if not hasattr(self, '_speed_unit_var'):
            self._speed_unit_var = ctk.StringVar(value="km/h")
        if not hasattr(self, '_efficiency_var'):
            self._efficiency_var = ctk.DoubleVar(value=0.85)

        grid = ctk.CTkFrame(s, fg_color='transparent')
        grid.pack(fill='x', padx=14, pady=(0, 10))
        grid.columnconfigure(1, weight=1)

        row = 0

        # Modèle moteur
        _field_label(grid, _("wizard.step2.motor_model")).grid(
            row=row, column=0, sticky='w', pady=5)
        motor_menu = ctk.CTkOptionMenu(
            grid, variable=self._motor_var, values=motor_names(),
            fg_color=COLORS['bg_light'], button_color=COLORS['mauve'],
            font=ctk.CTkFont(size=12),
            command=self._on_motor_changed)
        motor_menu.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=5)
        row += 1

        # KV
        _field_label(grid, _("wizard.step2.kv_value")).grid(
            row=row, column=0, sticky='w', pady=5)
        kv_frame = ctk.CTkFrame(grid, fg_color='transparent')
        kv_frame.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=5)
        kv_frame.columnconfigure(0, weight=1)
        ctk.CTkEntry(kv_frame, textvariable=self._kv_var,
                     placeholder_text=_("wizard.step2.kv_placeholder"),
                     fg_color=COLORS['bg_light'],
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky='ew')
        self._kv_hint = ctk.CTkLabel(
            kv_frame, text="", font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'])
        self._kv_hint.grid(row=1, column=0, sticky='w')
        self._update_kv_hint(self._motor_var.get())
        row += 1

        # ── Transmission ─────────────────────────────────────────────────────
        _field_label(grid, _("wizard.step2.transmission")).grid(
            row=row, column=0, sticky='w', pady=5)
        trans_menu = ctk.CTkOptionMenu(
            grid, variable=self._trans_var, values=transmission_names(),
            fg_color=COLORS['bg_light'], button_color=COLORS['mauve'],
            font=ctk.CTkFont(size=12),
            command=self._on_trans_changed)
        trans_menu.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=5)
        row += 1

        # ── Séparateur section engrenage ─────────────────────────────────────
        sep = ctk.CTkFrame(grid, height=1, fg_color=COLORS['bg_light'])
        sep.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(4, 2))
        row += 1

        # ── Pignon moteur ────────────────────────────────────────────────────
        _field_label(grid, _("wizard.step2.pinion_teeth")).grid(
            row=row, column=0, sticky='w', pady=4)
        self._pinion_entry = ctk.CTkEntry(
            grid, textvariable=self._pinion_var,
            placeholder_text=_("wizard.step2.pinion_placeholder"),
            fg_color=COLORS['bg_light'], font=ctk.CTkFont(size=12))
        self._pinion_entry.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=4)
        self._pinion_entry.bind("<KeyRelease>", lambda e: self._on_teeth_changed())
        row += 1

        # ── Poulie roue ──────────────────────────────────────────────────────
        _field_label(grid, _("wizard.step2.wheel_teeth")).grid(
            row=row, column=0, sticky='w', pady=4)
        self._wheel_teeth_entry = ctk.CTkEntry(
            grid, textvariable=self._wheel_teeth_var,
            placeholder_text=_("wizard.step2.wheel_teeth_placeholder"),
            fg_color=COLORS['bg_light'], font=ctk.CTkFont(size=12))
        self._wheel_teeth_entry.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=4)
        self._wheel_teeth_entry.bind("<KeyRelease>", lambda e: self._on_teeth_changed())
        row += 1

        # ── Ratio calculé automatiquement (hint) ─────────────────────────────
        self._ratio_auto_hint = ctk.CTkLabel(
            grid, text="", font=ctk.CTkFont(size=10, slant='italic'),
            text_color=COLORS['accent_blue'])
        self._ratio_auto_hint.grid(row=row, column=1, sticky='w', padx=(8, 0))
        row += 1

        # ── Ratio manuel (fallback si pas de pignon/poulie) ──────────────────
        _field_label(grid, _("wizard.step2.gear_ratio_or_teeth")).grid(
            row=row, column=0, sticky='w', pady=4)
        self._ratio_entry = ctk.CTkEntry(
            grid, textvariable=self._ratio_var,
            fg_color=COLORS['bg_light'], font=ctk.CTkFont(size=12))
        self._ratio_entry.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=4)
        row += 1

        # ── Séparateur section roue ──────────────────────────────────────────
        sep2 = ctk.CTkFrame(grid, height=1, fg_color=COLORS['bg_light'])
        sep2.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(4, 2))
        row += 1

        # ── Diamètre roue + unité ────────────────────────────────────────────
        _field_label(grid, _("wizard.step2.wheel_diameter")).grid(
            row=row, column=0, sticky='w', pady=4)
        diam_frame = ctk.CTkFrame(grid, fg_color='transparent')
        diam_frame.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=4)
        diam_frame.columnconfigure(0, weight=1)
        ctk.CTkEntry(diam_frame, textvariable=self._wheel_var,
                     placeholder_text=_("wizard.step2.wheel_diam_placeholder"),
                     fg_color=COLORS['bg_light'],
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky='ew')
        ctk.CTkOptionMenu(
            diam_frame, variable=self._wheel_unit_var, values=["mm", "inches"],
            fg_color=COLORS['bg_light'], button_color=COLORS['mauve'],
            font=ctk.CTkFont(size=11), width=80,
        ).grid(row=0, column=1, sticky='e', padx=(6, 0))
        self._wheel_hint = ctk.CTkLabel(
            diam_frame, text="", font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'])
        self._wheel_hint.grid(row=1, column=0, sticky='w', columnspan=2)
        self._update_wheel_hint(self._motor_var.get())
        row += 1

        # ── Unité de vitesse ─────────────────────────────────────────────────
        _field_label(grid, _("wizard.step2.speed_unit")).grid(
            row=row, column=0, sticky='w', pady=4)
        ctk.CTkSegmentedButton(
            grid, values=["km/h", "mph"],
            variable=self._speed_unit_var,
            fg_color=COLORS['bg_light'],
            selected_color=COLORS['mauve'], selected_hover_color=COLORS['mauve_hover'],
            font=ctk.CTkFont(size=12),
        ).grid(row=row, column=1, sticky='w', padx=(8, 0), pady=4)
        row += 1

        # ── Séparateur section efficacité ────────────────────────────────────
        sep3 = ctk.CTkFrame(grid, height=1, fg_color=COLORS['bg_light'])
        sep3.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(4, 2))
        row += 1

        # ── Efficacité transmission ──────────────────────────────────────────
        _field_label(grid, _("wizard.step2.efficiency")).grid(
            row=row, column=0, sticky='w', pady=4)
        eff_frame = ctk.CTkFrame(grid, fg_color='transparent')
        eff_frame.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=4)
        eff_frame.columnconfigure(0, weight=1)
        self._eff_slider = ctk.CTkSlider(
            eff_frame, from_=0.70, to=0.95,
            variable=self._efficiency_var, number_of_steps=25,
            button_color=COLORS['mauve'], button_hover_color=COLORS['mauve_hover'],
            command=self._on_efficiency_changed)
        self._eff_slider.grid(row=0, column=0, sticky='ew')
        self._eff_label = ctk.CTkLabel(
            eff_frame, text=f"{int(self._efficiency_var.get()*100)}%",
            font=ctk.CTkFont(size=11, weight='bold'),
            text_color=COLORS['mauve'], width=40)
        self._eff_label.grid(row=0, column=1, padx=(6, 0))
        self._eff_hint = ctk.CTkLabel(
            eff_frame, text="", font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'])
        self._eff_hint.grid(row=1, column=0, sticky='w', columnspan=2)
        self._on_efficiency_changed(self._efficiency_var.get())

        # ── Appliquer les états initiaux ─────────────────────────────────────
        self._on_trans_changed(self._trans_var.get())
        self._on_teeth_changed()

    def _on_motor_changed(self, name: str):
        self._update_kv_hint(name)
        self._update_wheel_hint(name)

    def _update_kv_hint(self, name: str):
        if not hasattr(self, '_kv_hint'):
            return
        from gui.wizard_data import get_motor
        try:
            m = get_motor(name)
            lo, hi = m["kv_range"]
            self._kv_hint.configure(text=f"Plage typique : {lo}–{hi} KV")
        except KeyError:
            self._kv_hint.configure(text="")

    def _update_wheel_hint(self, name: str):
        if not hasattr(self, '_wheel_hint'):
            return
        from gui.wizard_data import get_motor
        try:
            m = get_motor(name)
            hw = m.get("wheel_mm")
            if hw:
                self._wheel_hint.configure(text=f"Hub intégré : {hw} mm (laisser vide = auto)")
            else:
                self._wheel_hint.configure(text="Entrez le diamètre de votre roue de traction")
        except KeyError:
            self._wheel_hint.configure(text="")

    def _on_trans_changed(self, name: str):
        if not hasattr(self, '_ratio_entry'):
            return
        if name == "Direct Drive":
            self._ratio_var.set("1.0")
            self._ratio_entry.configure(state='disabled')
            if hasattr(self, '_pinion_entry'):
                self._pinion_entry.configure(state='disabled')
                self._wheel_teeth_entry.configure(state='disabled')
        else:
            # Ratio manuel actif uniquement si pas de pignon/poulie
            self._pinion_entry.configure(state='normal')
            self._wheel_teeth_entry.configure(state='normal')
            self._on_teeth_changed()

    def _on_teeth_changed(self):
        """Met à jour le ratio auto et grise le ratio manuel si les dents sont renseignées."""
        if not hasattr(self, '_ratio_entry') or not hasattr(self, '_ratio_auto_hint'):
            return
        p_txt = self._pinion_var.get().strip()
        w_txt = self._wheel_teeth_var.get().strip()
        if p_txt and w_txt:
            try:
                p, w = int(p_txt), int(w_txt)
                if p > 0 and w > 0:
                    ratio = w / p
                    self._ratio_auto_hint.configure(
                        text=_("wizard.step2.ratio_auto_hint").format(ratio=ratio))
                    self._ratio_entry.configure(state='disabled')
                    return
            except ValueError:
                pass
        self._ratio_auto_hint.configure(text="")
        # Ratio manuel réactivé si Direct Drive non sélectionné
        if hasattr(self, '_trans_var') and self._trans_var.get() != "Direct Drive":
            self._ratio_entry.configure(state='normal')

    def _on_efficiency_changed(self, value):
        pct = int(round(float(value) * 100))
        if hasattr(self, '_eff_label'):
            self._eff_label.configure(text=f"{pct}%")
        if hasattr(self, '_eff_hint'):
            self._eff_hint.configure(
                text=_("wizard.step2.efficiency_hint").format(pct=pct))

    # ── Étape 3 — Batterie ────────────────────────────────────────────────────

    def _build_step3(self):
        s = self._content_scroll
        _section_label(s, _("wizard.step3.title")).pack(padx=14, pady=(14, 10), anchor='w')

        if not hasattr(self, '_battery_var'):
            self._battery_var = ctk.StringVar(value=battery_names()[0])
        if not hasattr(self, '_cap_var'):
            self._cap_var = ctk.StringVar(value="")

        grid = ctk.CTkFrame(s, fg_color='transparent')
        grid.pack(fill='x', padx=14, pady=(0, 10))
        grid.columnconfigure(1, weight=1)

        row = 0

        # Modèle batterie
        _field_label(grid, _("wizard.step3.battery_model")).grid(
            row=row, column=0, sticky='w', pady=5)
        bat_menu = ctk.CTkOptionMenu(
            grid, variable=self._battery_var, values=battery_names(),
            fg_color=COLORS['bg_light'], button_color=COLORS['mauve'],
            font=ctk.CTkFont(size=12),
            command=self._on_battery_changed)
        bat_menu.grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=5)
        row += 1

        # Hint tension
        self._bat_hint = ctk.CTkLabel(
            grid, text="", font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'], anchor='w')
        self._bat_hint.grid(row=row, column=1, sticky='w', padx=(8, 0))
        self._update_bat_hint(self._battery_var.get())
        row += 1

        # Capacité (optionnelle)
        _field_label(grid, _("wizard.step3.capacity")).grid(
            row=row, column=0, sticky='w', pady=5)
        ctk.CTkEntry(
            grid, textvariable=self._cap_var,
            placeholder_text=_("wizard.step3.capacity_placeholder"),
            fg_color=COLORS['bg_light'],
            font=ctk.CTkFont(size=12)
        ).grid(row=row, column=1, sticky='ew', padx=(8, 0), pady=5)

    def _on_battery_changed(self, name: str):
        self._update_bat_hint(name)

    def _update_bat_hint(self, name: str):
        if not hasattr(self, '_bat_hint'):
            return
        from gui.wizard_data import get_battery
        try:
            b = get_battery(name)
            self._bat_hint.configure(
                text=f"{b['chemistry']}  {b['cells']}S — "
                     f"{b['nominal_v']} V nom / {b['max_v']} V max / {b['min_v']} V min")
        except KeyError:
            self._bat_hint.configure(text="")

    # ── Étape 4 — Résumé ──────────────────────────────────────────────────────

    def _build_step4(self):
        s = self._content_scroll
        if self._result is None:
            ctk.CTkLabel(s, text="Aucun résultat — retournez à l'étape précédente.",
                         text_color=COLORS['danger']).pack(padx=14, pady=20)
            return

        r   = self._result
        cfg = r.config.motor_a

        _section_label(s, _("wizard.step4.title")).pack(padx=14, pady=(14, 4), anchor='w')
        ctk.CTkLabel(s, text=_("wizard.step4.subtitle"),
                     font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary']
                     ).pack(padx=14, pady=(0, 10), anchor='w')

        # ── Grille de résultats ───────────────────────────────────────────────
        res_frame = ctk.CTkFrame(s, fg_color=COLORS['bg_light'], corner_radius=8)
        res_frame.pack(fill='x', padx=14, pady=(0, 10))
        res_frame.columnconfigure(1, weight=1)

        rows_data = [
            (_("wizard.step4.max_current"),
             f"{r.max_current_a:.1f}", _("wizard.step4.unit_a"), COLORS['accent_orange']),
            (_("wizard.step4.max_speed"),
             f"{r.speed_display:.1f}", r.speed_unit, COLORS['accent_green']),
            (_("wizard.step4.gear_ratio_used"),
             f"{r.gear_ratio_used:.2f}", _("wizard.step4.unit_ratio"), COLORS['accent_blue']),
            (_("wizard.step4.temp_fet"),
             f"{cfg.limits.temp_fet_max:.0f}", _("wizard.step4.unit_deg"), COLORS['accent']),
            (_("wizard.step4.ramp_up"),
             f"{cfg.ramp.ramp_up_time:.1f}", _("wizard.step4.unit_s"), COLORS['accent_blue']),
            (_("wizard.step4.max_duty"),
             f"{cfg.limits.max_duty * 100:.0f}", _("wizard.step4.unit_pct"), COLORS['mauve']),
            (_("wizard.step4.foc_mode"),
             cfg.foc.mode.name, "", COLORS['text_primary']),
            (_("wizard.step4.battery_voltage"),
             f"{r.config.battery.voltage_max:.1f}", _("wizard.step4.unit_v"),
             COLORS['warning']),
            (_("wizard.step4.erpm"),
             f"{r.max_erpm:,.0f}", "", COLORS['text_secondary']),
            (_("wizard.step4.efficiency_row"),
             f"{int(r.transmission_efficiency * 100)}", _("wizard.step4.unit_pct"),
             COLORS['text_secondary']),
        ]
        for i, (lbl, val, unit, color) in enumerate(rows_data):
            _result_row(res_frame, lbl, val, unit, row=i, accent=color)
        # padding
        for col in range(3):
            res_frame.columnconfigure(col, pad=8)

        # ── Valeurs recadrées par les limites hardware (priorité maximale) ──────
        if r.clamped_warnings:
            clamp_frame = ctk.CTkFrame(s, fg_color=COLORS['bg_light'], corner_radius=8,
                                       border_width=2, border_color=COLORS['danger'])
            clamp_frame.pack(fill='x', padx=14, pady=(0, 8))
            ctk.CTkLabel(clamp_frame, text=_("wizard.step4.clamped_title"),
                         font=ctk.CTkFont(size=12, weight='bold'),
                         text_color=COLORS['danger']).pack(padx=12, pady=(8, 4), anchor='w')
            for cw in r.clamped_warnings:
                ctk.CTkLabel(clamp_frame, text=f"  {cw}",
                             font=ctk.CTkFont(size=11),
                             text_color=COLORS['danger'], anchor='w',
                             wraplength=560).pack(padx=12, pady=1, anchor='w')
            ctk.CTkFrame(clamp_frame, height=6, fg_color='transparent').pack()

        # ── Avertissements non bloquants ──────────────────────────────────────
        if r.warnings:
            warn_frame = ctk.CTkFrame(s, fg_color=COLORS['bg_light'], corner_radius=8,
                                      border_width=1, border_color=COLORS['warning'])
            warn_frame.pack(fill='x', padx=14, pady=(0, 10))
            ctk.CTkLabel(warn_frame, text=_("wizard.step4.warnings_title"),
                         font=ctk.CTkFont(size=12, weight='bold'),
                         text_color=COLORS['warning']).pack(padx=12, pady=(8, 4), anchor='w')
            for w in r.warnings:
                ctk.CTkLabel(warn_frame, text=f"  • {w}",
                             font=ctk.CTkFont(size=11),
                             text_color=COLORS['warning'], anchor='w',
                             wraplength=560).pack(padx=12, pady=1, anchor='w')
            ctk.CTkFrame(warn_frame, height=6, fg_color='transparent').pack()

        # ── Boutons ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(s, fg_color='transparent')
        btn_row.pack(fill='x', padx=14, pady=(4, 14))

        ctk.CTkButton(
            btn_row, text=_("wizard.step4.recalculate"),
            command=lambda: self._show_step(3),
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=12), height=36, width=150
        ).pack(side='left')

        ctk.CTkButton(
            btn_row, text=_("wizard.step4.apply_button"),
            command=self._apply_config,
            fg_color=COLORS['accent_green'], hover_color=COLORS['success'],
            font=ctk.CTkFont(size=13, weight='bold'), height=40
        ).pack(side='right', fill='x', expand=True, padx=(12, 0))

    # ── Étape 5 — Application ─────────────────────────────────────────────────

    def _apply_config(self):
        if self._result is None or self._applying:
            return
        self._applying = True
        self._btn_next.configure(state='disabled')
        self._btn_back.configure(state='disabled')

        # Affiche la barre de progression
        self._apply_progress.pack(fill='x', padx=16, pady=(0, 4))
        self._apply_progress.set(0)
        self._set_status(_("wizard.apply.progress"))

        threading.Thread(target=self._apply_worker, daemon=True).start()

    def _apply_worker(self):
        """Thread de fond : envoie les trames WRITE_CONFIG."""
        result  = self._result
        cfg     = result.config
        transport = self._transport

        # Sections à écrire : motor, limits, ramp, battery (pour A, B, global)
        #   - motor → ctrl 0 et 1 (SEC_MOTOR)
        #   - limits → ctrl 0 et 1 (SEC_LIMITS)
        #   - ramp   → ctrl 0 et 1 (SEC_RAMP)
        #   - battery → ctrl 127 (global) (SEC_BATTERY)
        sections = [
            ("Motor A",   0,   SEC_MOTOR,   cfg.motor_a),
            ("Motor B",   1,   SEC_MOTOR,   cfg.motor_b),
            ("Limits A",  0,   SEC_LIMITS,  cfg.motor_a.limits),
            ("Limits B",  1,   SEC_LIMITS,  cfg.motor_b.limits),
            ("Ramp A",    0,   SEC_RAMP,    cfg.motor_a.ramp),
            ("Ramp B",    1,   SEC_RAMP,    cfg.motor_b.ramp),
            ("Battery",  127,  SEC_BATTERY, cfg.battery),
        ]
        total   = len(sections)
        success = True

        if transport and transport.is_connected:
            for i, (section_name, ctrl_id, sec_id, config_obj) in enumerate(sections):
                label = _("wizard.apply.section").format(
                    section=section_name, i=i + 1, total=total)
                self.after(0, self._set_status, label)
                self.after(0, self._apply_progress.set, (i + 1) / total)
                try:
                    frame = build_write_config_frame(ctrl_id, sec_id, config_obj)
                    transport.send(frame)
                except Exception as e:
                    self.after(0, self._set_status,
                               _("wizard.apply.error").format(e=e), True)
                    success = False
                    break
                # Pause inter-section (laisser le firmware traiter)
                import time
                time.sleep(0.08)
        else:
            success = False
            self.after(0, self._set_status, _("wizard.apply.no_connection"))

        # Fin
        self.after(0, self._apply_progress.set, 1.0 if success else 0.0)
        if success:
            self.after(0, self._set_status, _("wizard.apply.success"))
            if self._on_applied:
                self.after(0, self._on_applied, result.config)
        self.after(0, self._on_apply_done, success)

    def _on_apply_done(self, success: bool):
        self._applying = False
        self._btn_back.configure(state='normal')
        if success:
            self.after(3000, self._apply_progress.pack_forget)
            # Proposer la sauvegarde du profil
            self.after(400, self._prompt_save_profile)

    def _prompt_save_profile(self):
        """Dialogue 'Sauvegarder ce profil ?' après application réussie."""
        if self._result is None:
            return
        # Nom suggéré automatiquement : "Mon Setup 5045-8S" ou similaire
        motor  = getattr(self, '_motor_var',   None)
        bat    = getattr(self, '_battery_var', None)
        m_name = motor.get()  if motor  else "Moteur"
        b_name = bat.get()    if bat    else "Batterie"
        suggested = f"Mon Setup {m_name}-{b_name}"

        try:
            name = simpledialog.askstring(
                _("wizard.save_profile.title"),
                f"{_('wizard.save_profile.question')}\n\n{_('wizard.save_profile.name_label')}",
                initialvalue=suggested,
                parent=self.winfo_toplevel(),
            )
        except Exception:
            return   # fenêtre fermée ou CTk non disponible

        if not name or not name.strip():
            return   # l'utilisateur a annulé → aucune modification

        name = name.strip()
        try:
            ok = save_profile(name, self._result.config)
            if ok:
                self._set_status(
                    _("wizard.save_profile.success").format(name=name))
            else:
                self._set_status(
                    _("wizard.save_profile.error").format(e="Échec écriture"), error=True)
        except Exception as e:
            self._set_status(
                _("wizard.save_profile.error").format(e=e), error=True)

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _set_status(self, msg: str, error: bool = False):
        self._status_var.set(msg)
        color = COLORS['danger'] if error else COLORS['text_secondary']
        self._status_lbl.configure(text_color=color)
