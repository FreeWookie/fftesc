from gui.panels.config_panel import INPUT_CONTROL_FIELDS, SPEED_PID_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("input_control", _("config.tab_section.input_control"), COLORS['accent'], INPUT_CONTROL_FIELDS, COLORS['accent']),
    ("speed_pid", _("config.tab_section.speed_pid"), COLORS['accent_green'], SPEED_PID_FIELDS, COLORS['accent_green']),
]
MOTOR_SPECIFIC = False
SECTION_KEYS = ["input_control", "speed_pid"]
