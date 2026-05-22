from gui.panels.config_panel import CAN_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("can", _("config.tab_section.can"), COLORS['accent'], CAN_FIELDS, COLORS['accent']),
]
MOTOR_SPECIFIC = False
SECTION_KEYS = ["can"]
