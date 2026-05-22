from gui.panels.config_panel import LIMITS_FIELDS, RAMP_FIELDS, BRAKE_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("limits", _("config.tab_section.limits"), COLORS['warning'], LIMITS_FIELDS, COLORS['warning']),
    ("ramp", _("config.tab_section.ramp"), COLORS['accent_blue'], RAMP_FIELDS, COLORS['accent_blue']),
    ("brake", _("config.tab_section.brake"), COLORS['accent_orange'], BRAKE_FIELDS, COLORS['accent_orange']),
]
MOTOR_SPECIFIC = True
SECTION_KEYS = ["limits", "ramp", "brake"]
