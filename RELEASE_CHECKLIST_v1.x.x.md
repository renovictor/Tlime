# RELEASE CHECKLIST v1.x.x

## 1. Pre-check

- [ ] Confirm `version.py` updated (`CURRENT_VERSION`, `__version__`, `VERSION_HISTORY`).
- [ ] Confirm `README.md` version and release notes are aligned.
- [ ] Confirm required assets exist (logo/icon files).
- [ ] Confirm `requirements.txt` is up to date.
- [ ] Confirm working tree is clean except intended release changes.

## 2. Quick run validation

- [ ] Install dependencies: `python -m pip install -r requirements.txt`.
- [ ] Launch app: `python tlime.py`.
- [ ] Confirm splash screen shows for ~5 seconds.
- [ ] Confirm progress bar/status text updates during preload.
- [ ] Confirm main window opens without errors.
- [ ] Confirm log file is created/updated at `logs\tlime.log`.

## 3. Feature validation

- [ ] Smith chart renders and updates when input values change.
- [ ] Standing-wave and impedance plots render and update.
- [ ] Distance slider/spinbox stay synchronized.
- [ ] Animate button starts/stops sweep correctly.
- [ ] Quarter-wave helper produces expected guidance.
- [ ] Reset button restores default example values.
- [ ] Splash labels show logo/app/version/department/company/footer contact.

## 4. Git commit + tag

- [ ] `git add` release files and code changes.
- [ ] `git commit -m "Release v1.x.x"` (include release summary).
- [ ] `git tag -a v1.x.x -m "TLIME v1.x.x"`.
- [ ] Validate commit/tag references correct version.

## 5. Push

- [ ] `git push origin <branch>`.
- [ ] `git push origin v1.x.x`.
- [ ] Confirm remote branch and tag are visible.

## 6. Build single EXE (with branding)

- [ ] EXE name format: `<AppName>_v1.x.x.exe` (example: `TLIME_v1.0.0.exe`).
- [ ] Assign icon so it appears on:
  - [ ] Title bar icon
  - [ ] Taskbar icon
  - [ ] EXE file icon in Explorer
- [ ] Build command example:
  - [ ] `pyinstaller --noconfirm --onefile --windowed --name TLIME_v1.x.x --icon app.ico tlime.py`
- [ ] Bundle/ship logo assets if required by splash screen.
- [ ] Smoke test the built EXE on a clean environment.

## 7. Post-release verification

- [ ] Run released EXE and verify startup behavior/logging.
- [ ] Verify version displayed in UI matches tag and release notes.
- [ ] Verify no critical errors in startup/runtime logs.
- [ ] Archive release artifact and checksum.
- [ ] Publish release notes and distribute package.
