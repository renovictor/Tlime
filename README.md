# TLIME (Transmission Line Impedance Explorer)

TLIME is a PySide6 desktop tool for interactive transmission-line and Smith-chart exploration.  
It is designed for engineering education and quick impedance-matching studies with immediate visual feedback.

## Version

- Current version: **2026.11.1**
- Version source: `version.py`

## Main functions

- Interactive Smith chart with load/input reflection points and VSWR circle.
- Standing-wave and impedance plots versus position on the line.
- Live calculations for `ZL`, `Zin`, `Γ`, `VSWR`, wavelength, and physical distance.
- Quarter-wave transformer helper.
- Branded startup splash screen with module preload progress.
- Crash/activity logging to `logs\tlime.log` for troubleshooting.

## Install libraries

From this project folder:

```powershell
python -m pip install -r requirements.txt
```

## Run the app

```powershell
python tlime.py
```

## How to operate

1. Set transmission-line values (`Z0`, frequency, velocity factor).
2. Set load values (`RL`, `XL`).
3. Move the distance slider (or spinbox) to inspect input impedance along the line.
4. Use the display options to toggle VSWR circle and chart labels.
5. Use **Animate propagation** for continuous sweep.
6. Use **Quarter-wave transformer suggestion** for matching guidance.
7. Use **Load paper example** to restore the default demonstration values.

## Startup splash behavior

- Borderless, always-on-top splash for ~5 seconds.
- Gradient theme (dark navy to light purple).
- Shows company/logo area, app metadata, animated progress, and live module-loading status.
- Optional module preload failures (`NumPy`, `Matplotlib`, `Pillow`, `python-docx`) are skipped without blocking startup.

## Logs and troubleshooting

- Runtime and crash logs are saved to:
  - `logs\tlime.log`
- If the app crashes, check the latest entries in that file first.
