import customtkinter as ctk
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.styles.colors import COLORS


CHART_MAX_POINTS = 100

CHART_COLORS = {
    'voltage': '#0ea5e9',
    'current': '#e94560',
    'rpm': '#22c55e',
    'temp_fet': '#f59e0b',
    'temp_motor': '#ef4444',
    'duty': '#00d27a',
}


class ChartCard(ctk.CTkFrame):
    def __init__(self, parent, title="---", unit="", chart_key="", color=COLORS['accent'], **kwargs):
        super().__init__(parent, **kwargs)
        self._color = color
        self._chart_key = chart_key
        self._history = deque(maxlen=CHART_MAX_POINTS)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        value_frame = ctk.CTkFrame(self, fg_color='transparent', width=130)
        value_frame.grid(row=0, column=0, sticky='ns', padx=(5, 0))
        value_frame.grid_propagate(False)

        self._title_label = ctk.CTkLabel(value_frame, text=title, font=ctk.CTkFont(size=10), text_color=COLORS['text_secondary'])
        self._title_label.pack(pady=(6, 0))

        self._value_label = ctk.CTkLabel(value_frame, text="---", font=ctk.CTkFont(size=18, weight='bold'), text_color=color)
        self._value_label.pack(pady=(0, 0))

        self._unit_label = ctk.CTkLabel(value_frame, text=unit, font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary'])
        self._unit_label.pack(pady=(0, 6))

        self._chart_color = CHART_COLORS.get(chart_key, color)
        self._fig = Figure(figsize=(2.4, 1.1), dpi=80)
        self._ax = self._fig.add_subplot(111)
        self._apply_mpl_theme()
        self._line, = self._ax.plot([], [], color=self._chart_color, linewidth=1.2)
        self._fig.tight_layout(pad=0.3)

        self._chart_canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().grid(row=0, column=1, sticky='nsew', padx=(5, 5), pady=5)

    def _apply_mpl_theme(self):
        bg = COLORS.resolve('bg_medium')
        self._fig.patch.set_facecolor(bg)
        self._ax.set_facecolor(bg)
        tick_color = COLORS.resolve('text_secondary')
        spine_color = COLORS.resolve('bg_light')
        self._ax.tick_params(colors=tick_color, labelsize=6)
        self._ax.spines['top'].set_visible(False)
        self._ax.spines['right'].set_visible(False)
        self._ax.spines['bottom'].set_color(spine_color)
        self._ax.spines['left'].set_color(spine_color)

    def refresh_theme(self):
        self._apply_mpl_theme()
        self._chart_canvas.draw_idle()

    def set_value(self, value: float, decimals: int = 2):
        self._value_label.configure(text=f"{value:.{decimals}f}")
        self._history.append(value)
        self._redraw()

    def set_warning(self, is_warning: bool):
        color = COLORS['warning'] if is_warning else self._color
        self._value_label.configure(text_color=color)

    def _redraw(self):
        data = list(self._history)
        if not data:
            return
        self._line.set_data(range(len(data)), data)
        self._ax.relim()
        self._ax.autoscale_view()
        self._chart_canvas.draw_idle()
