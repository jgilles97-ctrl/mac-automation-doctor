# Mac Automation Doctor Free

**Your automation works in Terminal. Why does it fail in the background?**

Mac Automation Doctor Free is a local, read-only troubleshooting tool for macOS LaunchAgents and background automation. It looks for common deterministic problems that can make a script or scheduled job work manually but fail when `launchd` runs it.

## Download

**[Download Mac Automation Doctor Free 1.0](https://github.com/jgilles97-ctrl/mac-automation-doctor/releases/download/v1.0.0-free/mac-automation-doctor-free.zip)**

SHA-256: `2c621d6acad0553c3da744c88be2417b72594c2786873c595eb4fb807fa06249`

The release ZIP is the easiest download. The source is also available in this repository for inspection.

## What it checks

Mac Automation Doctor Free checks common failure points such as:

- LaunchAgent plist syntax and configuration problems;
- missing or invalid executables;
- duplicate launchd labels;
- missing working, output, or log directories;
- path and runtime-context problems;
- permissions that may prevent expected execution;
- local resource-pressure signals that can make background automation unreliable.

It is especially useful for the classic case where **a command works when you run it yourself, but the same automation does not behave correctly as a LaunchAgent**.

## Troubleshooting guides

If you want to understand the problem before running anything, start here:

- [LaunchAgent works in Terminal but not in launchd](docs/launchagent-works-in-terminal-not-launchd.md)
- [`launchctl bootstrap` failed: what to check before retrying](docs/launchctl-bootstrap-failed.md)
- [Why launchd cannot find a command that works in Terminal](docs/launchd-path-different-from-terminal.md)

These guides are intentionally useful without requiring a purchase or download.

## What it does *not* do

The diagnostic is intentionally conservative:

- no automatic repairs;
- no `sudo` requirement for its intended user-level scan;
- no process killing or service unloading;
- no telemetry;
- no cloud AI dependency;
- no network calls for diagnostic decisions.

It diagnoses and explains. You decide what to change.

## Quick start

1. Download and unzip the release.
2. Make sure Python 3.9 or newer is available on the Mac.
3. Run the included diagnostic from Terminal.
4. Review the findings before making any manual changes.

The tool is designed for people who use LaunchAgents, scripts, local automation, developer tools, or background jobs and want a safer first troubleshooting pass before editing system configuration.

## Common problems this can help investigate

- “My LaunchAgent works in Terminal but not in launchd.”
- “`launchctl bootstrap` failed and the error is not useful.”
- “My script cannot find a command when launchd runs it.”
- “My LaunchAgent writes no log/output.”
- “The plist looks right but the executable or directory is missing.”
- “Two jobs appear to be using the same label.”

## Free vs. Pro

The **Free** edition is the useful no-cost diagnostic entry point.

**Mac Automation Doctor Pro** expands the workflow with richer reports, historical scan comparison/diffing, and sanitized support-bundle export for deeper troubleshooting. Pro is a separate paid Cenluma product; the Free edition remains independently useful and is not intentionally crippled to force an upgrade.

Cenluma: https://cenluma.com

## Privacy and safety

Diagnostics run locally. The Free tool does not send diagnostic data to Cenluma or an AI service. As with any troubleshooting output, inspect files before sharing them with another person or service.

## Scope

This tool focuses on deterministic macOS background-automation diagnostics. It cannot guarantee a fix for every Apple security, MDM, sandbox, background-item, network, third-party-app, or permission problem, and it does not replace careful review of the specific automation you are troubleshooting.

## License / terms

See [TERMS.md](TERMS.md) for license and usage terms.

---

Built by **Cenluma** — practical local-first tools for automation, diagnostics, and everyday technology.