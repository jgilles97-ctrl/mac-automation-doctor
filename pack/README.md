# Mac Automation Doctor Free Edition

A read-only, local-first macOS diagnostic utility for user LaunchAgents and background automation setups.

## Features in Free Edition
- **User LaunchAgents Diagnostic**: Scans `~/Library/LaunchAgents` plists for syntax errors, missing labels, missing executable files/scripts, broken symlinks, insecure write permissions, missing log/working directories, and duplicate labels.
- **System Snapshot**: Inspects disk space, memory pressure, swap usage, load average, and common shell/runtime availability (`python3`, `zsh`, `bash`, `node`, `ruby`, `perl`, `osascript`, `shortcuts`).
- **Clean JSON & Markdown Outputs**: Produces structured `report.json` and human-readable `report.md` diagnostic summaries locally.
- **Strict Safety Commitments**: Local-first, zero network calls, zero telemetry, zero model requirements, and no mutation of inspected launchd/system configuration or processes. The tool only creates the report files you request.

## Usage

### Run Free Scan
```bash
python3 mac_automation_doctor_free.py
```
By default, reports are written to `~/Desktop/Mac-Automation-Doctor-Free-Reports/YYYYMMDD-HHMMSS/`.

### Options
```bash
# Specify custom output directory
python3 mac_automation_doctor_free.py --output /path/to/report_dir

# Output Markdown report directly to terminal stdout
python3 mac_automation_doctor_free.py --stdout
```

## Upgrade to Mac Automation Doctor Pro
To unlock system-wide and optional Apple launchd scopes, interactive HTML reports, historical diffs, richer PATH/context diagnostics, and sanitized support bundle export, upgrade to **Mac Automation Doctor Pro**.

The Free Edition does not hard-code a temporary storefront. Set `MAC_AUTOMATION_DOCTOR_PRO_URL` when a current Pro destination is available; leaving it unset does not affect any diagnostic behavior.
