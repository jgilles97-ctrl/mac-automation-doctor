#!/usr/bin/env python3
"""
Mac Automation Doctor Free Edition v1
Read-only, local-first macOS user LaunchAgents background automation diagnostic utility.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import plistlib
import re
import shutil
import stat
import subprocess
import sys
from collections import Counter
from typing import Any

SCHEMA = "MAC_AUTOMATION_DOCTOR_FREE_REPORT_V1"
DEFAULT_UPGRADE_URL = ""
UPGRADE_URL = os.environ.get("MAC_AUTOMATION_DOCTOR_PRO_URL", DEFAULT_UPGRADE_URL).strip() or DEFAULT_UPGRADE_URL

# Finding definitions table for Free Edition
FINDING_CATALOG: dict[str, dict[str, str]] = {
    "plist_parse_error": {
        "severity": "HIGH",
        "title": "Invalid Property List Syntax",
        "why_it_matters": "launchd cannot parse this plist file due to XML/binary formatting errors, causing the background service to fail entirely at boot/login.",
        "remediation_guidance": "Run `plutil -lint <plist_path>` in Terminal to see the exact line/syntax error, then edit the plist file to fix malformed tags or structures.",
    },
    "missing_label": {
        "severity": "MEDIUM",
        "title": "Missing Service Label Key",
        "why_it_matters": "launchd uses the `Label` string key as a unique identifier for job registration and management. Plists without a Label may fail to register or behave unpredictably.",
        "remediation_guidance": "Add a unique reverse-DNS label string (e.g. `<key>Label</key><string>com.user.myservice</string>`) to the plist file.",
    },
    "program_path_missing": {
        "severity": "CRITICAL",
        "title": "Referenced Executable Missing",
        "why_it_matters": "The specified executable binary or script path does not exist on disk, causing launchd spawn failures (`posix_spawn` error 2) whenever triggered.",
        "remediation_guidance": "Verify the script or executable path. Reinstall the missing executable, update `Program` or `ProgramArguments` in the plist, or unload/remove the service plist if no longer needed.",
    },
    "executable_symlink_broken": {
        "severity": "CRITICAL",
        "title": "Broken Executable Symlink",
        "why_it_matters": "The target binary path is a symbolic link pointing to a non-existent file, causing immediate launchd execution failures.",
        "remediation_guidance": "Re-create the missing target file, update the symlink to point to a valid binary path with `ln -sf`, or update the plist path directly.",
    },
    "executable_permissions_insecure": {
        "severity": "HIGH",
        "title": "Insecure Executable/Directory Permissions",
        "why_it_matters": "The binary or its parent directory is group- or world-writable, allowing unprivileged local users or scripts to alter or overwrite code executed by background jobs.",
        "remediation_guidance": "Restrict write permissions using `chmod 755 <path>` or `chmod 700 <path>` for binaries and parent directories.",
    },
    "executable_not_executable": {
        "severity": "HIGH",
        "title": "Target Path Is Not Executable",
        "why_it_matters": "The program path exists on disk but lacks execute permissions (`+x`) or points to a directory rather than an executable file.",
        "remediation_guidance": "Grant execute permissions using `chmod +x <path>` or point the plist to the actual binary file instead of a directory.",
    },
    "working_directory_missing": {
        "severity": "MEDIUM",
        "title": "Working Directory Does Not Exist",
        "why_it_matters": "launchd will fail to set the configured `WorkingDirectory` prior to process execution, which can break relative file references or cause process initialization failure.",
        "remediation_guidance": "Create the missing directory with `mkdir -p <dir_path>` or update `WorkingDirectory` in the plist to a valid path.",
    },
    "stdout_path_parent_missing": {
        "severity": "MEDIUM",
        "title": "Standard Output Log Directory Missing",
        "why_it_matters": "The directory meant to contain `StandardOutPath` does not exist, preventing launchd from capturing standard output logs.",
        "remediation_guidance": "Create the parent log directory using `mkdir -p <parent_directory>`.",
    },
    "stderr_path_parent_missing": {
        "severity": "MEDIUM",
        "title": "Standard Error Log Directory Missing",
        "why_it_matters": "The directory meant to contain `StandardErrorPath` does not exist, preventing launchd from recording error logs.",
        "remediation_guidance": "Create the parent log directory using `mkdir -p <parent_directory>`.",
    },
    "duplicate_label": {
        "severity": "HIGH",
        "title": "Duplicate Service Label in User LaunchAgents",
        "why_it_matters": "Multiple launchd plist files share the exact same `Label`. launchd will only register one instance, leading to conflicting or non-deterministic service execution.",
        "remediation_guidance": "Assign unique reverse-DNS labels (e.g. `com.user.task1`, `com.user.task2`) to each distinct plist file.",
    },
    "job_disabled": {
        "severity": "INFO",
        "title": "Disabled Key Present in Plist",
        "why_it_matters": "The plist contains `Disabled=true`. This is only a property-list observation; it does not prove the persistent `launchctl disable` state or current Login Items & Extensions approval.",
        "remediation_guidance": "Confirm the job's actual enabled state before changing anything. Do not infer current launchctl or Background Items state from this plist key alone.",
    },
    "malformed_program_arguments": {
        "severity": "HIGH",
        "title": "Malformed Program / ProgramArguments",
        "why_it_matters": "The plist specifies `ProgramArguments` as empty, non-array, or containing non-string values, which launchd cannot interpret as a valid argument vector.",
        "remediation_guidance": "Ensure `ProgramArguments` is a non-empty array of strings. When `Program` is explicitly set, `ProgramArguments[0]` does not need to equal `Program`.",
    },
    "disk_space_low": {
        "severity": "HIGH",
        "title": "Home Volume Disk Space Low (< 10 GB)",
        "why_it_matters": "Automations generating temporary files, downloading data, or appending to log files may crash or corrupt data when disk space is exhausted.",
        "remediation_guidance": "Free up disk space on the primary volume by removing old caches, temporary files, or unneeded archives.",
    },
    "memory_pressure_high": {
        "severity": "MEDIUM",
        "title": "Memory Free Percentage Low (< 15%)",
        "why_it_matters": "High memory pressure can cause OS throttling, heavy swap thrashing, or execution failure for memory-intensive background tasks.",
        "remediation_guidance": "Close unnecessary foreground applications or reschedule heavy background jobs to avoid simultaneous memory consumption.",
    },
    "swap_usage_high": {
        "severity": "MEDIUM",
        "title": "High Swap Usage (> 4000 MB)",
        "why_it_matters": "Elevated swap usage indicates RAM overcommitment, which significantly degrades background process execution speed and overall system responsiveness.",
        "remediation_guidance": "Identify memory-heavy processes using Activity Monitor or `top` and restart or optimize them.",
    },
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def run_readonly(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 127, "", type(e).__name__


def home_redact(value: str, home: pathlib.Path) -> str:
    s = str(value)
    hp = str(home)
    if s == hp:
        return "~"
    if s.startswith(hp + os.sep):
        return "~" + s[len(hp) :]
    return s


def sanitize_value(val: Any, home: pathlib.Path | None = None) -> Any:
    if home is None:
        home = pathlib.Path.home()
    user_name = os.environ.get("USER", home.name)
    if isinstance(val, str):
        res = val
        if str(home) in res:
            res = res.replace(str(home), "~")
        if user_name and user_name != "root" and f"/Users/{user_name}" in res:
            res = res.replace(f"/Users/{user_name}", "~")
        if home.name and f"/Users/{home.name}" in res:
            res = res.replace(f"/Users/{home.name}", "~")

        res = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+", "Bearer [REDACTED]", res)
        res = re.sub(
            r"(?i)(--?(?:api[_-]?key|token|secret|password|passwd|auth))\s+([^\s,;]+)",
            r"\1 [REDACTED]",
            res,
        )
        res = re.sub(
            r"(?i)\b(api[_-]?key|bearer|token|secret|password|passwd|auth)\b\s*[:=]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            res,
        )
        res = re.sub(r"(https?://)([^:]+):([^@]+)@", r"\1[REDACTED]:[REDACTED]@", res)
        res = re.sub(r"([?&](?:token|key|secret)=)[^&]+", r"\1[REDACTED]", res)
        return res
    elif isinstance(val, dict):
        return {k: sanitize_value(v, home) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_value(v, home) for v in val]
    return val


def console_user() -> str:
    rc, out, _ = run_readonly(["/usr/bin/stat", "-f", "%Su", "/dev/console"], 3)
    return out if rc == 0 and out else "unknown"


def get_runtime_presence() -> dict[str, dict[str, Any]]:
    runtimes = [
        ("python3", ["/usr/bin/python3", "--version"]),
        ("zsh", ["/bin/zsh", "--version"]),
        ("bash", ["/bin/bash", "--version"]),
        ("node", ["node", "--version"]),
        ("ruby", ["/usr/bin/ruby", "--version"]),
        ("perl", ["/usr/bin/perl", "--version"]),
        ("osascript", ["/usr/bin/osascript", "-e", "return 1"]),
        ("shortcuts", ["/usr/bin/shortcuts", "list"]),
    ]
    res: dict[str, dict[str, Any]] = {}
    for name, cmd in runtimes:
        bin_path = shutil.which(cmd[0])
        if bin_path:
            rc, out, err = run_readonly([bin_path] + cmd[1:], 3)
            ver_line = (out or err).splitlines()[0] if (out or err) else "present"
            res[name] = {"present": True, "path": bin_path, "version_info": ver_line[:80]}
        else:
            res[name] = {"present": False, "path": None, "version_info": None}
    return res


def system_snapshot(home: pathlib.Path) -> dict[str, Any]:
    rc, macos, _ = run_readonly(["/usr/bin/sw_vers", "-productVersion"], 3)
    rc2, build, _ = run_readonly(["/usr/bin/sw_vers", "-buildVersion"], 3)
    rc3, pressure, _ = run_readonly(["/usr/bin/memory_pressure", "-Q"], 5)
    free_pct = None
    if rc3 == 0:
        m = re.search(r"System-wide memory free percentage:\s*(\d+)%", pressure)
        if m:
            free_pct = int(m.group(1))

    rc4, swap, _ = run_readonly(["/usr/sbin/sysctl", "-n", "vm.swapusage"], 3)
    swap_used_mb = None
    if rc4 == 0:
        m = re.search(r"used\s*=\s*([0-9.]+)([MGT])", swap, re.I)
        if m:
            value = float(m.group(1))
            unit = m.group(2).upper()
            swap_used_mb = round(
                value * (1024 if unit == "G" else 1024 * 1024 if unit == "T" else 1), 1
            )

    du = shutil.disk_usage(home)
    disk_free_gb = round(du.free / (1024**3), 2)
    disk_total_gb = round(du.total / (1024**3), 2)

    try:
        load1, load5, load15 = os.getloadavg()
        load = [round(load1, 2), round(load5, 2), round(load15, 2)]
    except Exception:
        load = None

    env_path = os.environ.get("PATH", "")
    path_dirs = [p for p in env_path.split(os.pathsep) if p]
    common_dirs = ["/usr/bin", "/bin", "/usr/sbin", "/sbin", "/usr/local/bin", "/opt/homebrew/bin"]
    missing_common = [d for d in common_dirs if pathlib.Path(d).is_dir() and d not in path_dirs]

    system_warnings: list[str] = []
    if disk_free_gb < 10.0:
        system_warnings.append("disk_space_low")
    if free_pct is not None and free_pct < 15:
        system_warnings.append("memory_pressure_high")
    if swap_used_mb is not None and swap_used_mb > 4000.0:
        system_warnings.append("swap_usage_high")

    return {
        "macos_version": macos if rc == 0 else "unknown",
        "macos_build": build if rc2 == 0 else "unknown",
        "console_user": console_user(),
        "memory_free_percent": free_pct,
        "swap_used_mb": swap_used_mb,
        "home_disk_free_gb": disk_free_gb,
        "home_disk_total_gb": disk_total_gb,
        "load_average_1_5_15": load,
        "path_dirs": path_dirs,
        "missing_common_path_dirs": missing_common,
        "runtimes": get_runtime_presence(),
        "warnings": system_warnings,
    }


def first_program(obj: dict[str, Any]) -> tuple[str | None, str | None]:
    p = obj.get("Program")
    args = obj.get("ProgramArguments")

    p_str = p.strip() if isinstance(p, str) and p.strip() else None
    args_str = None
    if isinstance(args, list) and args and isinstance(args[0], str) and args[0].strip():
        args_str = args[0].strip()

    first = p_str or args_str
    return first, p_str


def check_executable_security(p: pathlib.Path) -> list[str]:
    warnings: list[str] = []
    try:
        st = p.stat()
        if not (st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)) and not p.is_dir():
            warnings.append("executable_not_executable")
        if p.is_dir():
            warnings.append("executable_not_executable")
        if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            warnings.append("executable_permissions_insecure")

        parent_st = p.parent.stat()
        if parent_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            if "executable_permissions_insecure" not in warnings:
                warnings.append("executable_permissions_insecure")
    except Exception:
        pass
    return warnings


def path_status(raw: str | None, home: pathlib.Path) -> dict[str, Any]:
    if not raw:
        return {"kind": "missing", "display": None, "exists": None, "is_symlink": False}
    expanded = os.path.expanduser(raw)
    p = pathlib.Path(expanded)
    if os.path.isabs(expanded):
        is_sym = p.is_symlink()
        exists = p.exists()
        return {
            "kind": "absolute",
            "display": home_redact(str(p), home),
            "exists": exists,
            "is_symlink": is_sym,
            "basename": p.name,
        }
    which = shutil.which(raw)
    return {
        "kind": "command_or_relative",
        "display": raw,
        "exists": which is not None,
        "resolved_path": home_redact(which, home) if which else None,
        "is_symlink": pathlib.Path(which).is_symlink() if which else False,
        "basename": pathlib.Path(raw).name,
    }


def scan_plist(path: pathlib.Path, home: pathlib.Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "scope": "user_launch_agent",
        "plist": home_redact(str(path), home),
        "parse_ok": False,
        "label": path.stem,
        "program": {"kind": "unknown", "display": None, "exists": None},
        "warnings": [],
    }

    if path.is_symlink() and not path.exists():
        row["warnings"].append("plist_parse_error")
        row["parse_error_type"] = "BrokenPlistSymlink"
        return row

    try:
        with path.open("rb") as f:
            obj = plistlib.load(f)
    except Exception as e:
        row["warnings"].append("plist_parse_error")
        row["parse_error_type"] = type(e).__name__
        return row

    row["parse_ok"] = True

    label = obj.get("Label")
    if isinstance(label, str) and label.strip():
        row["label"] = label.strip()
    else:
        row["warnings"].append("missing_label")

    disabled = obj.get("Disabled")
    if disabled is True:
        row["warnings"].append("job_disabled")
        row["disabled"] = True

    program_raw, explicit_p = first_program(obj)
    row["program"] = path_status(program_raw, home)

    p_args = obj.get("ProgramArguments")
    if p_args is not None:
        if not isinstance(p_args, list) or not p_args or not all(isinstance(x, str) for x in p_args):
            row["warnings"].append("malformed_program_arguments")
    if program_raw is None:
        row["warnings"].append("program_path_missing")
    else:
        prog_info = row["program"]
        if prog_info["kind"] == "absolute":
            p_obj = pathlib.Path(os.path.expanduser(program_raw))
            if p_obj.is_symlink() and not p_obj.exists():
                row["warnings"].append("executable_symlink_broken")
            elif not p_obj.exists():
                row["warnings"].append("program_path_missing")
            else:
                for sec_w in check_executable_security(p_obj):
                    if sec_w not in row["warnings"]:
                        row["warnings"].append(sec_w)
        elif prog_info["kind"] == "command_or_relative" and not prog_info["exists"]:
            row["warnings"].append("program_path_missing")

    wd = obj.get("WorkingDirectory")
    if isinstance(wd, str) and wd.strip():
        wd_path = pathlib.Path(os.path.expanduser(wd.strip()))
        row["working_directory"] = {
            "display": home_redact(str(wd_path), home),
            "exists": wd_path.exists(),
        }
        if not wd_path.exists():
            row["warnings"].append("working_directory_missing")

    for key, out_key in (("StandardOutPath", "stdout_path"), ("StandardErrorPath", "stderr_path")):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            p = pathlib.Path(os.path.expanduser(value.strip()))
            row[out_key] = home_redact(str(p), home)
            parent_exists = p.parent.exists()
            row[out_key + "_parent_exists"] = parent_exists
            if not parent_exists:
                row["warnings"].append(out_key + "_parent_missing")

    run_at_load = bool(obj.get("RunAtLoad", False))
    keep_alive = obj.get("KeepAlive", False)
    row["run_at_load"] = run_at_load
    row["keep_alive"] = keep_alive
    return row


def collect_user_services(home: pathlib.Path) -> list[dict[str, Any]]:
    user_agents = home / "Library" / "LaunchAgents"
    rows: list[dict[str, Any]] = []
    if not user_agents.is_dir():
        return rows

    try:
        plists = sorted(user_agents.glob("*.plist"))
    except Exception:
        return rows

    for path in plists:
        rows.append(scan_plist(path, home))

    counts = Counter(r["label"] for r in rows if r.get("parse_ok") and r.get("label"))
    for row in rows:
        if counts.get(row.get("label"), 0) > 1:
            if "duplicate_label" not in row["warnings"]:
                row["warnings"].append("duplicate_label")
            row["duplicate_label_count"] = counts[row["label"]]

    return rows


def build_finding_details(warning_code: str) -> dict[str, str]:
    catalog_entry = FINDING_CATALOG.get(
        warning_code,
        {
            "severity": "MEDIUM",
            "title": warning_code.replace("_", " ").title(),
            "why_it_matters": "Diagnostic issue detected in user background automation setup.",
            "remediation_guidance": "Review the service configuration plist and associated files.",
        },
    )
    return {
        "code": warning_code,
        "severity": catalog_entry["severity"],
        "title": catalog_entry["title"],
        "why_it_matters": catalog_entry["why_it_matters"],
        "remediation_guidance": catalog_entry["remediation_guidance"],
    }


def summarize(services: list[dict[str, Any]], system_warnings: list[str]) -> dict[str, Any]:
    warning_counts = Counter()
    severity_counts = Counter({"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0})

    for sys_w in system_warnings:
        warning_counts[sys_w] += 1
        sev = FINDING_CATALOG.get(sys_w, {}).get("severity", "MEDIUM")
        severity_counts[sev] += 1

    for row in services:
        for warning in row.get("warnings") or []:
            warning_counts[warning] += 1
            sev = FINDING_CATALOG.get(warning, {}).get("severity", "MEDIUM")
            severity_counts[sev] += 1

    return {
        "service_count": len(services),
        "warning_counts": dict(sorted(warning_counts.items())),
        "severity_counts": dict(severity_counts),
        "services_with_warnings": sum(1 for r in services if r.get("warnings")),
        "parse_failures": sum(1 for r in services if not r.get("parse_ok")),
    }


def markdown_report(report: dict[str, Any]) -> str:
    sysinfo = report["system"]
    summary = report["summary"]
    lines = [
        "# Mac Automation Doctor Free Edition Report",
        "",
        f"**Generated at:** {report['generated_at']}",
        f"**Schema:** {report['schema']}",
        "**Edition:** Free (User LaunchAgents Scope)",
        "",
        "## System Overview",
        f"- **macOS:** {sysinfo['macos_version']} (Build {sysinfo['macos_build']})",
        f"- **Console User:** `{sysinfo['console_user']}`",
        f"- **Memory Free:** {sysinfo['memory_free_percent']}%",
        f"- **Swap Used:** {sysinfo['swap_used_mb']} MB",
        f"- **Home Disk Free:** {sysinfo['home_disk_free_gb']} GB / {sysinfo['home_disk_total_gb']} GB",
        f"- **Load Average (1/5/15m):** {sysinfo['load_average_1_5_15']}",
        "",
        "## Summary Metrics",
        f"- **User Services Scanned:** {summary['service_count']}",
        f"- **Services with Warnings:** {summary['services_with_warnings']}",
        f"- **Plist Parse Failures:** {summary['parse_failures']}",
        "",
        "### Severity Breakdown",
    ]

    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        count = summary["severity_counts"].get(sev, 0)
        lines.append(f"- **{sev}:** {count}")

    lines += ["", "### Warning Counts"]
    if summary["warning_counts"]:
        for name, count in summary["warning_counts"].items():
            lines.append(f"- `{name}`: {count}")
    else:
        lines.append("- None")

    if sysinfo.get("warnings"):
        lines += ["", "## System Findings"]
        for sys_w in sysinfo["warnings"]:
            det = build_finding_details(sys_w)
            lines += [
                f"### [{det['severity']}] {det['title']} (`{sys_w}`)",
                f"- **Why this matters:** {det['why_it_matters']}",
                f"- **Remediation guidance:** {det['remediation_guidance']}",
                "",
            ]

    lines += ["", "## User Service Findings"]
    findings = [r for r in report["services"] if r.get("warnings")]
    if not findings:
        lines.append("No launchd warnings found in user LaunchAgents.")
    else:
        for row in findings:
            label = row.get("label", "unknown")
            scope = row.get("scope", "user_launch_agent")
            plist = row.get("plist", "unknown")
            prog = row.get("program", {}).get("display", "N/A")

            lines += [f"### Service: `{label}` ({scope})", f"- **Plist:** `{plist}`", f"- **Program:** `{prog}`", ""]
            for w in row.get("warnings", []):
                det = build_finding_details(w)
                lines += [
                    f"#### [{det['severity']}] {det['title']} (`{w}`)",
                    f"- **Why this matters:** {det['why_it_matters']}",
                    f"- **Remediation guidance:** {det['remediation_guidance']}",
                    "",
                ]

    lines += [
        "## Upgrade to Mac Automation Doctor Pro",
        "Need complete, enterprise-grade macOS background diagnostics?",
        "Upgrade to Mac Automation Doctor Pro to unlock:",
        "- **System-Wide Scopes:** Scan `/Library/LaunchAgents` and `/Library/LaunchDaemons`",
        "- **Apple System Scopes:** Scan `/System/Library` background services (`--include-apple`)",
        "- **PATH & Context Diagnostics:** Identify launchd-vs-Terminal environment mismatches",
        "- **Rich Interactive HTML Reports:** Self-contained, styled `report.html` dashboards",
        "- **Historical Comparison / Diff:** Track new, resolved, and persistent findings over time (`--diff`)",
        "- **Sanitized Support Bundle:** Export safe `.tar.gz` diagnostic bundles for tech support (`--export-support-bundle`)",
        "",
        (f"Learn more or upgrade at: {UPGRADE_URL}" if UPGRADE_URL else "Pro storefront URL: not configured yet (set MAC_AUTOMATION_DOCTOR_PRO_URL after the live listing exists)."),
        "",
        "## Usage & Safety Notice",
        "Mac Automation Doctor Free Edition does not mutate inspected launchd/system configuration or terminate processes. It only creates the requested local report files.",
        "Review each recommendation manually before altering launchd plists or system configurations.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Mac Automation Doctor Free Edition - Read-only macOS user LaunchAgents diagnostic"
    )
    ap.add_argument("--output", type=pathlib.Path, help="Directory to save generated reports")
    ap.add_argument("--stdout", action="store_true", help="Print Markdown report directly to stdout")
    ap.add_argument("--include-apple", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--diff", type=pathlib.Path, help=argparse.SUPPRESS)
    ap.add_argument("--export-support-bundle", type=pathlib.Path, help=argparse.SUPPRESS)

    args, unknown = ap.parse_known_args()

    # If user requests Pro-only flags, print informative upgrade notice
    pro_requested = []
    if args.include_apple:
        pro_requested.append("--include-apple")
    if args.diff:
        pro_requested.append("--diff")
    if args.export_support_bundle:
        pro_requested.append("--export-support-bundle")

    if pro_requested:
        print(f"Notice: The option(s) {', '.join(pro_requested)} require Mac Automation Doctor Pro.")
        if UPGRADE_URL:
            print(f"Upgrade to Pro at {UPGRADE_URL} to unlock advanced system-wide diagnostics, HTML reports, historical diffs, and support bundle exports.")
        else:
            print("Pro storefront URL is not configured yet.")

    home = pathlib.Path.home()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.output or (home / "Desktop" / "Mac-Automation-Doctor-Free-Reports" / stamp)).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    system_info = system_snapshot(home)
    services = collect_user_services(home)
    summary = summarize(services, system_info.get("warnings", []))

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "edition": "FREE",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "read_only": True,
        "network_used": False,
        "model_used": False,
        "system": system_info,
        "summary": summary,
        "services": services,
        "upgrade_info": {
            "pro_features": [
                "System-Wide LaunchAgents & LaunchDaemons scanning (/Library/LaunchAgents, /Library/LaunchDaemons)",
                "Apple System background services scanning (/System/Library)",
                "launchd vs Terminal PATH context mismatch detection",
                "Self-contained interactive HTML reports (report.html)",
                "Historical report comparison & diff analysis (--diff)",
                "Sanitized support bundle export (.tar.gz)",
            ],
            "upgrade_url": UPGRADE_URL or None,
        },
    }

    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = markdown_report(report)
    md_path.write_text(md, encoding="utf-8")

    if args.stdout:
        print(md)
    else:
        print("MAC_AUTOMATION_DOCTOR_FREE=PASS")
        print(f"report_json={json_path}")
        print(f"report_md={md_path}")
        print(f"services_scanned={summary['service_count']}")
        print(f"services_with_warnings={summary['services_with_warnings']}")
        print(f"upgrade_url={UPGRADE_URL or 'NOT_CONFIGURED'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
