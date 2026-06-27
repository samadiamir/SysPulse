# SysPulse

A modern desktop system monitoring and hardware diagnostics application built with Python and PySide6.

SysPulse provides real-time insights into system performance, hardware specifications, resource utilization, and overall system health through a clean, glassmorphism user interface.

---

## Features

### Dashboard
- Live CPU and Memory circular gauges with real-time percentage
- Disk usage, Battery status and Network activity stat cards
- Storage partition table with usage details
- **Customisable** - toggle visibility of each widget section

### Performance Monitoring
- Live CPU and Memory time-series charts (pyqtgraph)
- Per-core CPU usage bar breakdown
- Historical performance tracking with rolling 120-point window

### Processes
- Live process table sorted by CPU usage (top 80)
- Sortable columns - click any header to sort ascending/descending
- Search filter - type to filter by process name
- **Kill process** - select a row and click End Process (with confirmation)

### Hardware Information
- CPU model, cores, threads, architecture and frequency
- Installed memory (total, used, available)
- Operating system, hostname and machine details

### System Health
- Overall health status banner (Healthy / Warning / Critical)
- Per-subsystem health cards: CPU, Memory, Storage, Battery
- Actionable recommendations based on current resource levels

### Settings
- **Theme** - dark / light toggle with instant live preview
- **Accent Colour** - 8 colour presets
- **Font** - 6 typeface choices
- **Font Size** - slider from 10pt to 20pt
- **UI Density** - Compact / Normal / Large spacing
- **Language** - 7 languages
- **Update Interval** - slider from 500ms to 5000ms (debounced)
- All settings persist across restarts via QSettings

### Notification Alerts
- Desktop notifications when CPU, Memory, Disk or Battery cross thresholds
- 60-second cooldown per alert type to prevent spam
- Toggle on/off from the View menu

### Export Reports
- Export Snapshot as JSON (Ctrl+Shift+J)
- Export Snapshot as CSV (Ctrl+Shift+C)
- Auto-creates export directory if missing

---

## Installation

### Prerequisites
- Python 3.10 or newer
- pip (Python package manager)

### Quick Start

    pip install -r requirements.txt
    python main.py

### Dependencies

| Package | Purpose |
|---------|---------|
| PySide6 | Qt6 GUI framework |
| psutil | System and process metrics |
| pyqtgraph | Real-time performance charts |
| py-cpuinfo | Detailed CPU information |
| QtAwesome | Font Awesome icons in Qt |
| PyQtDarkTheme | Base dark/light theme |

---

## Project Structure

    SysPulse/
    |
    +-- main.py                    # Entry point
    |
    +-- core/                      # Data layer
    |   +-- snapshot.py            # Typed dataclasses
    |   +-- system_data.py         # Metrics + TTL cache
    |   +-- health_checker.py      # Threshold evaluator
    |
    +-- controller/                # Business logic
    |   +-- settings_manager.py    # QSettings preferences
    |   +-- updater.py             # Periodic data pump
    |   +-- alert_manager.py       # Notifications
    |   +-- exporter.py            # CSV/JSON export
    |
    +-- ui/                        # Presentation layer
    |   +-- styles.py              # Dual theme + density QSS
    |   +-- widgets.py             # Card, Gauge, Badge, Toggle
    |   +-- base_page.py           # ScrollablePage base
    |   +-- page_protocol.py       # PageSubscriber Protocol
    |   +-- main_window.py         # Application shell
    |   +-- dashboard_page.py      # Dashboard
    |   +-- performance_page.py    # Live charts
    |   +-- process_page.py        # Process viewer
    |   +-- hardware_page.py       # Hardware specs
    |   +-- health_page.py         # Health verdicts
    |   +-- settings_page.py       # Settings panel
    |   +-- customize_page.py      # Dashboard toggles
    |
    +-- tests/                     # 90 pytest tests
    |   +-- test_system_data.py
    |   +-- test_health_checker.py
    |   +-- test_updater.py
    |   +-- test_widgets.py
    |   +-- test_pages.py
    |
    +-- conftest.py
    +-- pytest.ini
    +-- requirements.txt
    +-- README.md

---

## Architecture

### Data Flow

    SystemData (psutil/cpuinfo)
           |
           v
      Snapshot (typed dataclass)
           |
           v
       Updater (QTimer, 1.5s tick)
           |
           +--> PageSubscriber.update_data(snapshot)
           |       +-- DashboardPage
           |       +-- PerformancePage
           |       +-- ProcessPage
           |       +-- HardwarePage
           |       +-- HealthPage
           |
           +--> AlertManager.check(snapshot)
           |       +--> notification signal
           |
           +--> ticked signal --> external consumers

### OOP Patterns

- **Typed Dataclasses** - Snapshot, MemoryInfo, DiskInfo, ProcessInfo, HealthResult
- **Protocol** - PageSubscriber enforces update_data contract at subscribe time
- **Encapsulation** - private internals, read-only properties, public methods only
- **Singleton** - SettingsManager.instance()
- **Observer** - Qt Signals/Slots
- **Template Method** - ScrollablePage base class
- **Lazy Construction** - pages built on first navigation (~400ms startup)
- **TTL Cache** - disk I/O cached for 4 seconds

---

## Testing

    # Run all tests
    python -m pytest -v

    # Run with timeout
    python -m pytest -v --timeout=30

    # Run specific test file
    python -m pytest tests/test_health_checker.py -v

**90 tests** across 5 test files, running headless (offscreen).

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Q | Quit |
| F5 | Refresh now |
| Ctrl+Shift+J | Export snapshot as JSON |
| Ctrl+Shift+C | Export snapshot as CSV |

---

## Configuration

Settings are stored via QSettings and persist across restarts:
- **Windows**: Registry
- **macOS**: ~/Library/Preferences/
- **Linux**: ~/.config/

---

## License

MIT License

---

## Acknowledgements

- [psutil](https://github.com/giampaolo/psutil)
- [PyQtGraph](https://github.com/pyqtgraph/pyqtgraph)
- [py-cpuinfo](https://github.com/workhorsy/py-cpuinfo)
- [QtAwesome](https://github.com/spyder-ide/qtawesome)
- [PyQtDarkTheme](https://github.com/5yutan5/PyQtDarkTheme)
