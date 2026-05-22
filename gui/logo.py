"""
gui/logo.py — Gestion des logos FFTESC (Normal et Connecté)
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageTk
import customtkinter as ctk
from ftesc.resources import get_resource_path

# Chemins des fichiers SVG (résolus au runtime pour supporter PyInstaller)
TITLE_SVG_PATH = Path(get_resource_path("fftesc_title.svg"))
TITLE_ON_SVG_PATH = Path(get_resource_path("fftesc_title_on.svg"))
ICON_SVG_PATH = Path(get_resource_path("fftesc_logo.svg"))
ICON_ON_SVG_PATH = Path(get_resource_path("fftesc_logo_on.svg"))

# Cache: en mode frozen, utiliser un répertoire utilisateur writable
if getattr(sys, 'frozen', False):
    CACHE_DIR = Path(os.path.join(os.path.expanduser("~"), ".fftesc", "logo_cache"))
else:
    CACHE_DIR = Path(get_resource_path("logo_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def convert_svg_to_png(svg_path: Path, png_path: Path, size: tuple = (80, 80)):
    """Convertit un SVG en PNG pour l'affichage."""
    try:
        import cairosvg
        scale = 2
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=size[0] * scale,
            output_height=size[1] * scale
        )
        return True
    except ImportError:
        print("Erreur: cairosvg non installé.")
        return False
    except Exception as e:
        print(f"Erreur conversion {svg_path}: {e}")
        return False

def load_logo_image(svg_path: Path, size: tuple = (80, 80)) -> ctk.CTkImage | None:
    """Charge une image SVG et retourne un CTkImage."""
    if not svg_path.exists():
        return None

    cache_filename = f"{svg_path.stem}_{size[0]}x{size[1]}.png"
    cache_path = CACHE_DIR / cache_filename

    if not cache_path.exists():
        if not convert_svg_to_png(svg_path, cache_path, size):
            return None

    try:
        img = Image.open(cache_path)
        img = img.resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception as e:
        print(f"Erreur chargement image {cache_path}: {e}")
        return None

def create_title_widget(parent, size: tuple = (150, 50), connected: bool = False) -> ctk.CTkLabel:
    """Crée le widget titre avec le logo adapté (Normal ou ON)."""
    svg_path = TITLE_ON_SVG_PATH if connected else TITLE_SVG_PATH
    logo_img = load_logo_image(svg_path, size)

    if logo_img:
        try:
            label = ctk.CTkLabel(parent, image=logo_img, text="")
            label._ftesc_image = logo_img
            return label
        except Exception:
            pass
    # Fallback texte
    color = '#00d27a' if connected else '#e94560'
    return ctk.CTkLabel(
        parent, text=f"\u26a1 FFTESC {'(ON)' if connected else ''}",
        font=ctk.CTkFont(size=24, weight='bold'),
        text_color=color
    )

def set_app_icon(window, connected: bool = False):
    """Définit l'icône de la fenêtre principale (window + dock/taskbar)."""
    svg_path = ICON_ON_SVG_PATH if connected else ICON_SVG_PATH

    if not svg_path.exists():
        print(f"ERREUR ICÔNE: Fichier introuvable : {svg_path}")
        return

    images = []
    for size in [(32, 32), (64, 64), (128, 128)]:
        cache_filename = f"{svg_path.stem}_{size[0]}x{size[1]}.png"
        cache_path = CACHE_DIR / cache_filename
        if not cache_path.exists() or cache_path.stat().st_size == 0:
            if not convert_svg_to_png(svg_path, cache_path, size):
                continue
        try:
            pil_img = Image.open(cache_path)
            pil_img = pil_img.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)
            images.append(photo)
        except Exception:
            pass

    if images:
        window.iconphoto(True, *images)
        window._ftesc_icons = images
        print(f"Icônes appliquées : {svg_path.name} ({len(images)} tailles)")
