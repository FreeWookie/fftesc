from gui.panels.config_panel import DUAL_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("dual_setup", _("config.tab_section.dual"), COLORS['accent_blue'], DUAL_FIELDS, COLORS['accent_blue']),
]
MOTOR_SPECIFIC = False
SECTION_KEYS = ["dual_setup"]
