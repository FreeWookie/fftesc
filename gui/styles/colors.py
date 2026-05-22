import customtkinter as ctk

_DARK = {
    'bg_dark': '#1e1e2e',
    'bg_medium': '#252540',
    'bg_light': '#2d2d4a',
    'accent': '#e94560',
    'accent_green': '#00d27a',
    'accent_blue': '#0ea5e9',
    'accent_orange': '#f59e0b',
    'text_primary': '#eef0f4',
    'text_secondary': '#9399b0',
    'danger': '#ef4444',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'mauve': '#7c5cfc',
    'mauve_hover': '#6246ea',
    'danger_hover': '#b91c1c',
}

_LIGHT = {
    'bg_dark': '#eef0f4',
    'bg_medium': '#f8f9fb',
    'bg_light': '#e0e4ec',
    'accent': '#dc2626',
    'accent_green': '#16a34a',
    'accent_blue': '#2563eb',
    'accent_orange': '#d97706',
    'text_primary': '#1e293b',
    'text_secondary': '#6b7280',
    'danger': '#dc2626',
    'success': '#16a34a',
    'warning': '#d97706',
    'mauve': '#7c3aed',
    'mauve_hover': '#6d28d9',
    'danger_hover': '#dc2626',
}

class _Colors:
    def __getitem__(self, key):
        return (_LIGHT[key], _DARK[key])

    def resolve(self, key):
        """Retourne une seule couleur hex pour le thème actuel (matplotlib/PIL)."""
        return _DARK[key] if ctk.get_appearance_mode() == 'Dark' else _LIGHT[key]

COLORS = _Colors()
