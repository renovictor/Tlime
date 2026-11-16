"""Central version and release history for TLIME."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


APP_NAME = "TLIME"
APP_TITLE = "Transmission Line Impedance Explorer"
COMPANY_NAME = "ASM International"
DEPARTMENT_NAME = "Engineering Department"
AUTHOR = "Victor Chingping Huang"
CONTACT = "victor.huang@asm.com"

CURRENT_VERSION = AppVersion(2026, 11, 1)
__version__ = str(CURRENT_VERSION)

VERSION_HISTORY: tuple[tuple[str, str], ...] = (
    (
        "2026.11.1",
        "UI refresh: exit button, improved standing-wave readability, phasor view, and manual 3D rotation.",
    ),
    ("1.0.0", "Initial PySide6 release with splash preloading and crash logging."),
)
