from gui.panels.config_panel import MOTOR_FIELDS, HALL_FIELDS, FOC_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("motor", _("config.tab_section.motor"), COLORS['accent_blue'], MOTOR_FIELDS, COLORS['accent_blue']),
    ("hall", _("config.tab_section.hall"), COLORS['accent_orange'], HALL_FIELDS, COLORS['accent_orange']),
    ("foc", _("config.tab_section.foc"), COLORS['accent'], FOC_FIELDS, COLORS['accent']),
]
MOTOR_SPECIFIC = True
SECTION_KEYS = ["motor", "hall", "foc"]
