# -*- coding: utf-8 -*-
"""
gui/app_icons.py — Chargement et application des icônes FFTESC.

Trois points d'entrée :
  • title_icon   : logo dans la barre de titre (CTkImage affiché dans un CTkLabel)
  • icon_app     : icône fenêtre système (barre des tâches / alt-tab)
  • dock_icon    : icône dock (Linux via wm_iconphoto avec image haute résolution)

Stratégie de résolution :
  1. logo_cache/<nom>.png  (PNG pré-rendu — le plus rapide)
  2. Rendu à la volée via cairosvg si disponible
  3. Fallback silencieux : aucune icône (l'app démarre quand même)

Aucun import CTk n'est fait ici — ce module est pur PIL/cairosvg
pour rester importable hors contexte graphique.
"""
from __future__ import annotations

import io
import os
import sys
import pathlib
from typing import Optional, TYPE_CHECKING

from PIL import Image, ImageTk
from ftesc.resources import get_resource_path

if TYPE_CHECKING:
    import customtkinter as ctk

# ── Chemins (résolus au runtime pour PyInstaller) ─────────────────────────────
_CACHE_DIR_BASE = pathlib.Path(
    os.path.join(os.path.expanduser("~"), ".fftesc", "logo_cache")
    if getattr(sys, 'frozen', False)
    else get_resource_path("logo_cache")
)
_CACHE_DIR_BASE.mkdir(parents=True, exist_ok=True)

_SVG_LOGO      = pathlib.Path(get_resource_path("fftesc_logo.svg"))
_SVG_LOGO_ON   = pathlib.Path(get_resource_path("fftesc_logo_on.svg"))
_SVG_TITLE     = pathlib.Path(get_resource_path("fftesc_title.svg"))
_SVG_TITLE_ON  = pathlib.Path(get_resource_path("fftesc_title_on.svg"))


# ── Chargeur générique ────────────────────────────────────────────────────────

def _load_png(name: str) -> Optional[Image.Image]:
    """Charge un PNG depuis logo_cache/, None si absent."""
    path = _CACHE_DIR_BASE / name
    if path.exists():
        try:
            return Image.open(path).convert("RGBA")
        except Exception:
            pass
    return None


def _render_svg(svg_path: pathlib.Path, w: int, h: int) -> Optional[Image.Image]:
    """Rend un SVG en PIL.Image via cairosvg. None si cairosvg absent."""
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(
            url=str(svg_path), output_width=w * 2, output_height=h * 2)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        return img.resize((w, h), Image.LANCZOS)
    except Exception:
        return None


def _load_logo(w: int, h: int) -> Optional[Image.Image]:
    """Charge le logo déconnecté à la taille demandée (cache → SVG → None)."""
    img = _load_png(f"fftesc_logo_{w}x{h}.png")
    if img is None:
        img = _render_svg(_SVG_LOGO, w, h)
    if img is not None and img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    return img


def _load_logo_on(w: int, h: int) -> Optional[Image.Image]:
    """Charge le logo connecté (_on) à la taille demandée."""
    img = _load_png(f"fftesc_logo_on_{w}x{h}.png")
    if img is None:
        img = _render_svg(_SVG_LOGO_ON, w, h)
    if img is not None and img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    return img or _load_logo(w, h)   # fallback sur la version off


def _load_title(w: int, h: int) -> Optional[Image.Image]:
    """Charge le logo-titre déconnecté à la taille demandée."""
    img = _load_png(f"fftesc_title_{w}x{h}.png")
    if img is None:
        img = _render_svg(_SVG_TITLE, w, h)
    if img is not None and img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    return img


def _load_title_on(w: int, h: int) -> Optional[Image.Image]:
    """Charge le logo-titre connecté (_on) à la taille demandée."""
    img = _load_png(f"fftesc_title_on_{w}x{h}.png")
    if img is None:
        img = _render_svg(_SVG_TITLE_ON, w, h)
    if img is not None and img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    return img or _load_title(w, h)  # fallback sur la version off


# ── API publique ──────────────────────────────────────────────────────────────

def make_title_ctk_image(w: int = 200, h: int = 60):
    """
    Retourne un ctk.CTkImage du logo-titre pour affichage dans la barre de titre.
    w × h : taille d'affichage logique (pixels indépendants du DPI).
    """
    try:
        import customtkinter as ctk
        light_img = _load_title(w, h)
        dark_img  = _load_title(w, h)
        if light_img and dark_img:
            return ctk.CTkImage(
                light_image=light_img,
                dark_image=dark_img,
                size=(w, h),
            )
    except Exception:
        pass
    return None


def make_logo_ctk_image(w: int = 32, h: int = 32):
    """Retourne un ctk.CTkImage du logo carré (état déconnecté)."""
    try:
        import customtkinter as ctk
        img = _load_logo(w, h)
        if img:
            return ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
    except Exception:
        pass
    return None


def make_title_ctk_image_on(w: int = 200, h: int = 54):
    """Retourne un ctk.CTkImage du logo-titre en état connecté (_on)."""
    try:
        import customtkinter as ctk
        img = _load_title_on(w, h)
        if img:
            return ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
    except Exception:
        pass
    return None


def make_connection_indicator_images(w: int = 200, h: int = 54) -> dict:
    """
    Pré-charge les deux états (off / on) du logo-titre.

    Retourne :
        {
            "disconnected": ctk.CTkImage | None,
            "connected":    ctk.CTkImage | None,
        }

    Le widget CTkLabel qui affiche le logo sidebar doit stocker ces deux
    images et les swapper via configure(image=...) à chaque changement d'état.
    """
    return {
        "disconnected": make_title_ctk_image(w, h),
        "connected":    make_title_ctk_image_on(w, h),
    }


def update_connection_indicator(label_widget, connected: bool,
                                images: dict) -> None:
    """
    Bascule l'image du CTkLabel logo entre l'état connecté et déconnecté.

    Paramètres
    ----------
    label_widget : ctk.CTkLabel — le widget logo dans la sidebar
    connected    : True si un ESC est connecté (ou simulateur actif)
    images       : dict retourné par make_connection_indicator_images()
    """
    if label_widget is None or images is None:
        return
    key = "connected" if connected else "disconnected"
    img = images.get(key)
    if img is None:
        img = images.get("disconnected")   # fallback ultime
    if img is not None:
        try:
            label_widget.configure(image=img)
        except Exception:
            pass


def apply_window_icons(window) -> None:
    """
    Applique les trois icônes sur la fenêtre principale CTk :

      1. icon_app  — icône barre des tâches / alt-tab  (wm_iconphoto)
      2. dock_icon — icône dock haute résolution        (wm_iconphoto avec 256×256)
      3. title_icon — logo dans la zone titre           (CTkLabel avec CTkImage)

    Appelé APRÈS que la fenêtre est affichée (update_idletasks recommandé).
    Silencieux en cas d'erreur.
    """
    _set_taskbar_icon(window)
    _set_title_logo(window)


def _set_taskbar_icon(window) -> None:
    """
    Définit l'icône système (barre des tâches, alt-tab, dock Linux).
    Utilise wm_iconphoto avec plusieurs résolutions pour que l'OS choisisse.
    """
    try:
        sizes    = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
        tk_imgs  = []
        for w, h in sizes:
            img = _load_logo(w, h)
            if img:
                tk_imgs.append(ImageTk.PhotoImage(img))
        if tk_imgs:
            # wm_iconphoto(True, ...) : True → applique à toutes les fenêtres Toplevel
            window.wm_iconphoto(True, *tk_imgs)
    except Exception:
        pass   # X11 non disponible, Wayland sans support, etc.


def _set_title_logo(window) -> None:
    """
    Place le logo-titre à gauche dans la barre de titre CTk.

    CTk ne supporte pas nativement un logo custom dans la barre de titre ;
    on crée un CTkLabel image flottant au-dessus du titlebar natif via
    place(), ancré en haut à gauche.
    """
    try:
        import customtkinter as ctk

        img = make_title_ctk_image(180, 44)
        if img is None:
            return

        lbl = ctk.CTkLabel(window, image=img, text="", fg_color="transparent",
                            cursor="arrow")
        # Positionné dans la zone titre interne du frame principal
        # row=0 grid du CTk host frame — on l'insère dans la sidebar header
        # Pour ne pas perturber le layout, on l'expose via un attribut public
        # et on laisse app.py décider où le placer.
        window._title_logo_widget = lbl
    except Exception:
        pass
