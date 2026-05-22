from gui.panels.config_panel import BATTERY_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("battery", _("config.tab_section.battery"), COLORS['accent_green'], BATTERY_FIELDS, COLORS['accent_green']),
]
MOTOR_SPECIFIC = False
SECTION_KEYS = ["battery"]
