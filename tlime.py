from __future__ import annotations

import cmath
import importlib
import logging
import math
import sys
import threading
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QMovie, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from version import (
    APP_NAME,
    APP_TITLE,
    AUTHOR,
    COMPANY_NAME,
    CONTACT,
    CURRENT_VERSION,
    DEPARTMENT_NAME,
    __version__,
)


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "tlime.log"
SPLASH_MINIMUM_MS = 5000
MODULE_LOAD_PLAN = (
    ("PySerial", "serial", False),
    ("Pandas", "pandas", False),
    ("OpenPyXL", "openpyxl", False),
    ("NumPy", "numpy", True),
    ("Matplotlib", "matplotlib", True),
    ("Pillow/PIL", "PIL", True),
    ("python-docx", "docx", True),
    ("guardian_tlog", "guardian_tlog", False),
    ("jsonl_to_excel", "jsonl_to_excel", False),
)


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(threadName)s | %(message)s")
    )
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(console_handler)

    logging.info("Logging initialized. Output file: %s", LOG_FILE)


def install_exception_hooks() -> None:
    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        QMessageBox.critical(
            None,
            f"{APP_NAME} Crash",
            (
                "The application encountered an unexpected error and must close.\n\n"
                f"Log file: {LOG_FILE}"
            ),
        )

    sys.excepthook = handle_exception

    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = handle_thread_exception


def get_logo_path() -> Path | None:
    candidates = (
        BASE_DIR / "ASM-logo-small.gif",
        BASE_DIR / "ASM-logo-small.png",
        BASE_DIR / "ASM-logo-small.jpg",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def get_icon() -> QIcon | None:
    candidates = (
        BASE_DIR / "app.ico",
        BASE_DIR / "ASM-logo-small.ico",
        BASE_DIR / "ASM-logo-small.png",
        BASE_DIR / "ASM-logo-small.gif",
    )
    for candidate in candidates:
        if candidate.exists():
            icon = QIcon(str(candidate))
            if not icon.isNull():
                return icon
    return None


class ModulePreloader(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_loading = Signal()

    def run(self) -> None:
        total = len(MODULE_LOAD_PLAN)
        for index, (label, module_name, optional) in enumerate(MODULE_LOAD_PLAN, start=1):
            self.status_changed.emit(f"Loading {label}...")
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError:
                if optional:
                    logging.info("Optional module skipped: %s", module_name)
                else:
                    logging.warning("Required module not found: %s", module_name)
            except Exception:
                if optional:
                    logging.info("Optional module failed: %s", module_name, exc_info=True)
                else:
                    logging.exception("Required module failed: %s", module_name)
            self.progress_changed.emit(int((index / total) * 100))
            self.msleep(170)
        self.status_changed.emit("Finalizing startup...")
        self.finished_loading.emit()


class SplashScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(860, 500)
        self._elapsed = QElapsedTimer()
        self._target_progress = 0
        self._build_ui()

        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(40)
        self.pulse_timer.timeout.connect(self._animate_progress)
        self.pulse_timer.start()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 20)
        root.setSpacing(15)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(20)
        top_grid.setVerticalSpacing(8)
        root.addLayout(top_grid)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(170, 120)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet(
            "background: rgba(255,255,255,0.08); border-radius: 10px;"
        )
        top_grid.addWidget(self.logo_label, 0, 0, 4, 1)

        app_name = QLabel(APP_NAME)
        app_name.setFont(QFont("Segoe UI", 30, QFont.Bold))
        app_name.setStyleSheet("color: #f7f6ff;")
        top_grid.addWidget(app_name, 0, 1)

        title_label = QLabel(APP_TITLE)
        title_label.setFont(QFont("Segoe UI", 13))
        title_label.setStyleSheet("color: #e5ddff;")
        top_grid.addWidget(title_label, 1, 1)

        details_label = QLabel(
            f"Version {CURRENT_VERSION}   |   {DEPARTMENT_NAME}   |   {COMPANY_NAME}"
        )
        details_label.setFont(QFont("Segoe UI", 11))
        details_label.setStyleSheet("color: #d4cbff;")
        top_grid.addWidget(details_label, 2, 1)

        self.status_label = QLabel("Starting up...")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #ffffff;")
        top_grid.addWidget(self.status_label, 3, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Loading... %p%")
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 10px;
                background: rgba(255,255,255,0.08);
                color: #ffffff;
                min-height: 22px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                border-radius: 9px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4ac6ff, stop:1 #b88cff);
            }
            """
        )
        root.addWidget(self.progress_bar)

        footer = QFrame()
        footer.setStyleSheet("background: rgba(0,0,0,0.28); border-radius: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.addWidget(
            QLabel(f"Author: {AUTHOR}  |  Contact: {CONTACT}"),
            alignment=Qt.AlignLeft,
        )
        footer_layout.itemAt(0).widget().setStyleSheet("color: #e8e6ff; font-size: 10pt;")
        root.addWidget(footer)

        logo_path = get_logo_path()
        if logo_path:
            if logo_path.suffix.lower() == ".gif":
                movie = QMovie(str(logo_path))
                if movie.isValid():
                    self.logo_label.setMovie(movie)
                    movie.start()
            current_pixmap = self.logo_label.pixmap()
            if current_pixmap is None or current_pixmap.isNull():
                self.logo_label.setPixmap(QPixmap(str(logo_path)))
                self.logo_label.setScaledContents(True)
        else:
            self.logo_label.setText("ASM")
            self.logo_label.setStyleSheet(
                "background: rgba(255,255,255,0.12); color: #ffffff;"
                "font-size: 34px; font-weight: 700; border-radius: 10px;"
            )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0f1234"))
        gradient.setColorAt(0.55, QColor("#2d2c7c"))
        gradient.setColorAt(1.0, QColor("#8f6dff"))
        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.center_on_screen()
        self._elapsed.start()

    def center_on_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)

    def _animate_progress(self) -> None:
        current = self.progress_bar.value()
        if current < self._target_progress:
            self.progress_bar.setValue(current + 1)
        elif current < 95:
            self.progress_bar.setValue(current + 1)

    def set_target_progress(self, value: int) -> None:
        self._target_progress = min(100, max(0, value))

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def elapsed_ms(self) -> int:
        if not self._elapsed.isValid():
            return 0
        return self._elapsed.elapsed()


def build_tlime_window_class(np, FigureCanvasQTAgg, Figure):
    @dataclass(frozen=True)
    class TLState:
        z0: float
        zl: complex
        distance_lambda: float
        frequency_mhz: float
        velocity_factor: float

        @property
        def gamma_load(self) -> complex:
            return (self.zl - self.z0) / (self.zl + self.z0)

        @property
        def beta_d(self) -> float:
            return 2.0 * math.pi * self.distance_lambda

        @property
        def gamma_at_input(self) -> complex:
            return self.gamma_load * cmath.exp(-2j * self.beta_d)

        @property
        def zin(self) -> complex:
            t = math.tan(self.beta_d)
            denominator = self.z0 + 1j * self.zl * t
            if abs(denominator) < 1e-12:
                return complex(float("inf"), float("inf"))
            return self.z0 * (self.zl + 1j * self.z0 * t) / denominator

        @property
        def vswr(self) -> float:
            mag = abs(self.gamma_load)
            if mag >= 1.0 - 1e-12:
                return float("inf")
            return (1.0 + mag) / (1.0 - mag)

        @property
        def wavelength_m(self) -> float:
            c = 299_792_458.0
            return self.velocity_factor * c / (self.frequency_mhz * 1e6)

    class MplCanvas(FigureCanvasQTAgg):
        def __init__(self, rows=1, cols=1, figsize=(7, 6)):
            self.figure = Figure(figsize=figsize, constrained_layout=True)
            self.axes = self.figure.subplots(rows, cols)
            super().__init__(self.figure)

    class SmithChartCanvas(MplCanvas):
        def __init__(self):
            super().__init__(figsize=(7.4, 7.0))
            self.ax = self.axes

        def draw_chart(self, state: TLState, show_vswr: bool, show_labels: bool):
            ax = self.ax
            ax.clear()
            theta = np.linspace(0, 2 * np.pi, 1000)
            ax.plot(np.cos(theta), np.sin(theta), color="#ffffff", lw=1.2)

            for r in [0, 0.2, 0.5, 1, 2, 5]:
                center = r / (1 + r)
                radius = 1 / (1 + r)
                x = center + radius * np.cos(theta)
                y = radius * np.sin(theta)
                mask = x * x + y * y <= 1.0001
                ax.plot(x[mask], y[mask], color="#8eb4ff", lw=0.7, alpha=0.75)
                if show_labels and r > 0:
                    ax.text((r - 1) / (r + 1), 0.018, f"r={r:g}", fontsize=7, color="#d9e4ff")

            r_values = np.logspace(-4, 4, 1000)
            for x_const in [0.2, 0.5, 1, 2, 5]:
                for sign in [1, -1]:
                    z = r_values + 1j * sign * x_const
                    gamma = (z - 1) / (z + 1)
                    ax.plot(gamma.real, gamma.imag, color="#7ec7d9", lw=0.7, alpha=0.65)
                    if show_labels:
                        idx = 120 if sign > 0 else 880
                        ax.text(
                            gamma.real[idx],
                            gamma.imag[idx],
                            f"x={sign*x_const:g}",
                            fontsize=7,
                            color="#d9e4ff",
                        )

            g0 = state.gamma_load
            gd = state.gamma_at_input
            mag = abs(g0)
            if show_vswr:
                ax.plot(
                    mag * np.cos(theta),
                    mag * np.sin(theta),
                    "--",
                    color="#ffd166",
                    lw=1.5,
                    label="Constant |Γ| / VSWR",
                )

            arc_t = np.linspace(cmath.phase(g0), cmath.phase(gd), 180)
            ax.plot(mag * np.cos(arc_t), mag * np.sin(arc_t), color="#4cc9f0", lw=2.2)
            ax.scatter([g0.real], [g0.imag], s=70, color="#ff6b6b", zorder=5, label="Load ΓL")
            ax.scatter([gd.real], [gd.imag], s=70, color="#82e0aa", zorder=5, label="Input Γ(d)")
            ax.plot([0, gd.real], [0, gd.imag], color="#82e0aa", lw=1.2)

            ax.axhline(0, color="#f0f0f0", lw=0.8)
            ax.axvline(0, color="#f0f0f0", lw=0.4, alpha=0.65)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlim(-1.08, 1.08)
            ax.set_ylim(-1.08, 1.08)
            ax.set_xlabel("Re{Γ}", color="#ecf2ff")
            ax.set_ylabel("Im{Γ}", color="#ecf2ff")
            ax.set_title("Interactive Smith Chart", color="#f8f9ff")
            ax.tick_params(colors="#d7dfff")
            ax.set_facecolor("#1b204b")
            ax.legend(loc="upper left", fontsize=8)
            self.figure.patch.set_facecolor("#1b204b")
            self.draw_idle()

    class WaveCanvas(MplCanvas):
        def __init__(self):
            super().__init__(3, 1, figsize=(6.5, 7.0))

        def draw_waves(self, state: TLState):
            axes = np.atleast_1d(self.axes)
            for ax in axes:
                ax.clear()
                ax.set_facecolor("#171c41")
                ax.tick_params(colors="#d7dfff")
                ax.xaxis.label.set_color("#ecf2ff")
                ax.yaxis.label.set_color("#ecf2ff")

            z = np.linspace(0, 1.0, 600)
            gamma = state.gamma_load
            beta_z = 2 * np.pi * z
            voltage = np.exp(1j * beta_z) + gamma * np.exp(-1j * beta_z)
            current = (np.exp(1j * beta_z) - gamma * np.exp(-1j * beta_z)) / state.z0
            zin_curve = state.z0 * (state.zl + 1j * state.z0 * np.tan(beta_z)) / (
                state.z0 + 1j * state.zl * np.tan(beta_z)
            )

            axes[0].plot(z, np.abs(voltage), color="#5dade2", label="|V(z)|")
            axes[0].axvline(state.distance_lambda, color="#ff6b6b", ls="--")
            axes[0].set_ylabel("Normalized voltage")
            axes[0].legend(facecolor="#121735", edgecolor="#4a5b9d", labelcolor="#eef2ff")

            axes[1].plot(z, np.abs(current) * state.z0, color="#c792ea", label="Z0·|I(z)|")
            axes[1].axvline(state.distance_lambda, color="#ff6b6b", ls="--")
            axes[1].set_ylabel("Normalized current")
            axes[1].legend(facecolor="#121735", edgecolor="#4a5b9d", labelcolor="#eef2ff")

            axes[2].plot(z, np.real(zin_curve), color="#57cc99", label="Re{Zin}")
            axes[2].plot(z, np.imag(zin_curve), color="#ffd166", label="Im{Zin}")
            axes[2].axvline(state.distance_lambda, color="#ff6b6b", ls="--")
            axes[2].set_xlabel("Distance from load toward generator [λ]")
            axes[2].set_ylabel("Impedance [Ω]")
            axes[2].set_ylim(-5 * state.z0, 5 * state.z0)
            axes[2].legend(
                ncol=2, facecolor="#121735", edgecolor="#4a5b9d", labelcolor="#eef2ff"
            )

            for ax in axes:
                ax.grid(True, alpha=0.24, color="#8ea6ff")
            self.figure.patch.set_facecolor("#171c41")
            self.draw_idle()

    class TLIMEWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} v{__version__} - {APP_TITLE}")
            self.resize(1450, 900)
            self.setStyleSheet(
                """
                QWidget {
                    background-color: #111533;
                    color: #eef1ff;
                    font-family: Segoe UI;
                    font-size: 10pt;
                }
                QGroupBox {
                    border: 1px solid #5063a7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 8px;
                    background-color: #1a214c;
                    font-weight: 600;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QDoubleSpinBox, QComboBox {
                    background-color: #111533;
                    border: 1px solid #6884d8;
                    border-radius: 4px;
                    padding: 3px 6px;
                }
                QPushButton {
                    background-color: #5c6fd8;
                    border: 1px solid #8397ff;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #6d80eb;
                }
                QPushButton:checked {
                    background-color: #8d65ff;
                }
                QLabel#resultLabel {
                    background-color: #0d122d;
                    border: 1px solid #5063a7;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: Consolas, monospace;
                }
                """
            )
            self._build_ui()
            self._connect_signals()
            self.update_all()

        @staticmethod
        def _float_box(value, minimum, maximum, decimals=3, suffix=""):
            box = QDoubleSpinBox()
            box.setRange(minimum, maximum)
            box.setDecimals(decimals)
            box.setValue(value)
            box.setSuffix(suffix)
            box.setSingleStep(0.1)
            return box

        def _build_ui(self):
            root = QWidget()
            self.setCentralWidget(root)
            main = QHBoxLayout(root)
            splitter = QSplitter(Qt.Horizontal)
            main.addWidget(splitter)

            control_scroll = QWidget()
            controls = QVBoxLayout(control_scroll)
            splitter.addWidget(control_scroll)

            line_group = QGroupBox("Transmission line and load")
            form = QFormLayout(line_group)
            self.z0 = self._float_box(50.0, 0.01, 10000, 3, " Ω")
            self.rl = self._float_box(30.0, -10000, 10000, 3, " Ω")
            self.xl = self._float_box(40.0, -10000, 10000, 3, " Ω")
            self.freq = self._float_box(13.56, 0.001, 100000, 4, " MHz")
            self.vf = self._float_box(1.0, 0.01, 1.0, 3)
            form.addRow("Characteristic Z0", self.z0)
            form.addRow("Load resistance RL", self.rl)
            form.addRow("Load reactance XL", self.xl)
            form.addRow("Frequency", self.freq)
            form.addRow("Velocity factor", self.vf)
            controls.addWidget(line_group)

            distance_group = QGroupBox("Position from load toward generator")
            dbox = QVBoxLayout(distance_group)
            self.distance_slider = QSlider(Qt.Horizontal)
            self.distance_slider.setRange(0, 500)
            self.distance_slider.setValue(0)
            self.distance_spin = self._float_box(0.0, 0.0, 0.5, 4, " λ")
            self.distance_spin.setSingleStep(0.005)
            row = QHBoxLayout()
            row.addWidget(self.distance_slider)
            row.addWidget(self.distance_spin)
            dbox.addLayout(row)
            self.animate = QPushButton("Animate propagation")
            self.animate.setCheckable(True)
            dbox.addWidget(self.animate)
            controls.addWidget(distance_group)

            display_group = QGroupBox("Display")
            display_layout = QVBoxLayout(display_group)
            self.show_vswr = QCheckBox("Show constant VSWR circle")
            self.show_vswr.setChecked(True)
            self.show_labels = QCheckBox("Show Smith chart labels")
            self.mode = QComboBox()
            self.mode.addItems(["Impedance", "Admittance"])
            display_layout.addWidget(self.show_vswr)
            display_layout.addWidget(self.show_labels)
            display_layout.addWidget(self.mode)
            controls.addWidget(display_group)

            result_group = QGroupBox("Calculated values")
            result_layout = QVBoxLayout(result_group)
            self.results = QLabel()
            self.results.setObjectName("resultLabel")
            self.results.setTextInteractionFlags(Qt.TextSelectableByMouse)
            result_layout.addWidget(self.results)
            controls.addWidget(result_group)

            match_group = QGroupBox("Matching helpers")
            match_layout = QVBoxLayout(match_group)
            self.quarter_button = QPushButton("Quarter-wave transformer suggestion")
            self.reset_button = QPushButton("Load paper example: 30 + j40 Ω")
            match_layout.addWidget(self.quarter_button)
            match_layout.addWidget(self.reset_button)
            controls.addWidget(match_group)
            controls.addStretch(1)

            tabs = QTabWidget()
            self.smith = SmithChartCanvas()
            self.waves = WaveCanvas()
            tabs.addTab(self.smith, "Smith chart")
            tabs.addTab(self.waves, "Standing waves and Zin")
            splitter.addWidget(tabs)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 1)
            splitter.setSizes([350, 1100])

            self.timer = QTimer(self)
            self.timer.setInterval(35)

        def _connect_signals(self):
            widgets = [self.z0, self.rl, self.xl, self.freq, self.vf, self.distance_spin]
            for widget in widgets:
                widget.valueChanged.connect(self.update_all)
            self.distance_slider.valueChanged.connect(self._slider_to_spin)
            self.distance_spin.valueChanged.connect(self._spin_to_slider)
            self.show_vswr.toggled.connect(self.update_all)
            self.show_labels.toggled.connect(self.update_all)
            self.mode.currentIndexChanged.connect(self.update_all)
            self.animate.toggled.connect(self._toggle_animation)
            self.timer.timeout.connect(self._animation_step)
            self.quarter_button.clicked.connect(self._quarter_wave_suggestion)
            self.reset_button.clicked.connect(self._load_example)

        def state(self) -> TLState:
            return TLState(
                z0=self.z0.value(),
                zl=complex(self.rl.value(), self.xl.value()),
                distance_lambda=self.distance_spin.value(),
                frequency_mhz=self.freq.value(),
                velocity_factor=self.vf.value(),
            )

        def _slider_to_spin(self, value):
            self.distance_spin.blockSignals(True)
            self.distance_spin.setValue(value / 1000.0)
            self.distance_spin.blockSignals(False)
            self.update_all()

        def _spin_to_slider(self, value):
            self.distance_slider.blockSignals(True)
            self.distance_slider.setValue(round(value * 1000))
            self.distance_slider.blockSignals(False)

        def _toggle_animation(self, active):
            self.animate.setText("Stop animation" if active else "Animate propagation")
            self.timer.start() if active else self.timer.stop()

        def _animation_step(self):
            value = self.distance_slider.value() + 2
            if value > self.distance_slider.maximum():
                value = 0
            self.distance_slider.setValue(value)

        @staticmethod
        def _complex_text(value: complex, unit=""):
            if not np.isfinite(value.real) or not np.isfinite(value.imag):
                return "∞"
            return f"{value.real:.4f} {value.imag:+.4f}j{unit}"

        def update_all(self, *_):
            s = self.state()
            if abs(s.zl + s.z0) < 1e-12:
                return
            self.smith.draw_chart(s, self.show_vswr.isChecked(), self.show_labels.isChecked())
            self.waves.draw_waves(s)

            z_norm = s.zl / s.z0
            y_load = 1 / s.zl if abs(s.zl) > 1e-12 else complex(float("inf"), 0)
            y_in = 1 / s.zin if abs(s.zin) > 1e-12 else complex(float("inf"), 0)
            gamma = s.gamma_load
            angle = math.degrees(cmath.phase(gamma))
            distance_m = s.distance_lambda * s.wavelength_m
            mode_lines = (
                f"ZL/Z0       = {self._complex_text(z_norm)}\n"
                f"Zin(d)      = {self._complex_text(s.zin, ' Ω')}"
                if self.mode.currentText() == "Impedance"
                else f"YL          = {self._complex_text(y_load, ' S')}\n"
                f"Yin(d)      = {self._complex_text(y_in, ' S')}"
            )
            vswr_text = "∞" if math.isinf(s.vswr) else f"{s.vswr:.4f}"
            self.results.setText(
                f"ZL          = {self._complex_text(s.zl, ' Ω')}\n"
                f"{mode_lines}\n"
                f"ΓL          = {self._complex_text(gamma)}\n"
                f"|ΓL|        = {abs(gamma):.5f}\n"
                f"∠ΓL         = {angle:.3f}°\n"
                f"VSWR        = {vswr_text}\n"
                f"λ           = {s.wavelength_m:.5f} m\n"
                f"Distance    = {distance_m:.5f} m"
            )

        def _quarter_wave_suggestion(self):
            s = self.state()
            if abs(s.zl.imag) > 1e-9:
                text = (
                    "A direct quarter-wave transformer requires a real resistance at "
                    "its connection plane. Move the position slider until Im{Zin} is "
                    "approximately zero, then calculate Zt = sqrt(Z0 · Re{Zin})."
                )
            elif s.zl.real <= 0:
                text = "The load resistance must be positive for this simple helper."
            else:
                zt = math.sqrt(s.z0 * s.zl.real)
                length = s.wavelength_m / 4
                text = (
                    f"Quarter-wave transformer characteristic impedance:\n"
                    f"Zt = sqrt({s.z0:.4f} × {s.zl.real:.4f}) = {zt:.4f} Ω\n\n"
                    f"Electrical length: 0.25 λ\n"
                    f"Physical length with VF={s.velocity_factor:.3f}: {length:.6f} m"
                )
            QMessageBox.information(self, "Quarter-wave transformer", text)

        def _load_example(self):
            self.z0.setValue(50.0)
            self.rl.setValue(30.0)
            self.xl.setValue(40.0)
            self.distance_spin.setValue(0.25)
            self.update_all()

    return TLIMEWindow


def start_main_window(app: QApplication, splash: SplashScreen, icon: QIcon | None) -> None:
    try:
        import numpy as np
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure

        TLIMEWindow = build_tlime_window_class(np, FigureCanvasQTAgg, Figure)
        window = TLIMEWindow()
        if icon:
            window.setWindowIcon(icon)
        window.show()
        splash.close()
        app.active_window = window
    except Exception:
        logging.exception("Failed to start main window")
        QMessageBox.critical(
            splash,
            "Startup Error",
            f"Unable to open the main window.\nSee logs at:\n{LOG_FILE}",
        )
        app.quit()


def main():
    configure_logging()
    install_exception_hooks()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon = get_icon()
    if icon:
        app.setWindowIcon(icon)

    splash = SplashScreen()
    if icon:
        splash.setWindowIcon(icon)
    splash.show()
    app.processEvents()

    preloader = ModulePreloader()
    splash.preloader = preloader

    preloader.status_changed.connect(splash.set_status)
    preloader.progress_changed.connect(splash.set_target_progress)

    def finalize_startup() -> None:
        splash.set_target_progress(100)
        remaining = max(0, SPLASH_MINIMUM_MS - splash.elapsed_ms())
        QTimer.singleShot(remaining, lambda: start_main_window(app, splash, icon))

    preloader.finished_loading.connect(finalize_startup)
    preloader.start()
    logging.info("%s v%s started", APP_NAME, __version__)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
