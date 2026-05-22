from gui.panels.config_panel import IMU_FIELDS
from gui.styles.colors import COLORS
from gui.i18n import _

SECTIONS = [
    ("imu", _("config.tab_section.imu"), COLORS['accent_orange'], IMU_FIELDS, COLORS['accent_orange']),
]
MOTOR_SPECIFIC = False
SECTION_KEYS = ["imu"]
