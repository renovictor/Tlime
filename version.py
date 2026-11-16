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
COMPANY_NAME = "ASM Company"
DEPARTMENT_NAME = "Engineering Department"
AUTHOR = "ASM Engineering Team"
CONTACT = "support@asm.example.com"

CURRENT_VERSION = AppVersion(1, 0, 0)
__version__ = str(CURRENT_VERSION)

VERSION_HISTORY: tuple[tuple[str, str], ...] = (
    ("1.0.0", "Initial PySide6 release with splash preloading and crash logging."),
)

