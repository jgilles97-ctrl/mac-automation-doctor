# `launchctl bootstrap` Failed on macOS: What to Check Before Retrying

A `launchctl bootstrap` failure can be frustrating because the returned error is often less specific than the underlying problem. Before repeatedly unloading and reloading the job, check the configuration and the files it depends on.

## 1. Confirm the plist itself is valid

```bash
plutil -lint ~/Library/LaunchAgents/com.example.job.plist
```

Fix syntax errors first. A plist that parses correctly can still contain incorrect paths or launchd settings, so this is only the first check.

## 2. Verify the job label

The `Label` should be unique for the launchd domain where the job is being loaded. Duplicate or stale jobs with the same label can make troubleshooting confusing.

## 3. Verify the executable in `Program` / `ProgramArguments`

Check that the referenced executable really exists:

```bash
ls -l /absolute/path/to/executable
```

If the job calls a script directly, verify its executable permission and interpreter line where applicable.

Do not assume `launchd` sees the same PATH, aliases, shell functions, or version-manager setup that your Terminal session sees.

## 4. Verify every referenced directory

Check directories used for:

- the working directory;
- standard output;
- standard error;
- application data;
- scripts or helper tools.

A missing or inaccessible directory can prevent the job from behaving as expected.

## 5. Make sure you are bootstrapping into the intended domain

User LaunchAgents and system LaunchDaemons belong to different launchd contexts. Confirm the plist belongs in the domain you are using and that you are troubleshooting the intended user/job.

## 6. Inspect current launchd state before another retry

A previous job instance or partial setup may still exist. Inspect the domain/job state rather than repeatedly issuing the same bootstrap command without changing anything.

If the failure is deterministic, another identical retry is unlikely to fix the root cause.

## 7. Consider modern macOS background-item rules

Apps on modern macOS can manage bundled helpers using Apple’s Service Management framework. If the LaunchAgent came from an installed application, manual plist manipulation may not be the app’s supported control path.

## If `bootstrap` reports error 5

A message such as `Bootstrap failed: 5: Input/output error` is a generic failure, not a diagnosis of a bad disk or a single cause. Note the job label and the time of the failure, then inspect recent launchd messages:

```bash
log show --last 10m --style compact --predicate 'process == "launchd"'
```

Compare entries near the failure with the job label, executable, and paths in the plist. An empty or unclear log does not rule out a cause. Review output for private paths or other sensitive details before sharing it.

If the job launches an app, plug-in, or installer downloaded from outside the App Store, you can read its quarantine attribute without changing it:

```bash
xattr -p com.apple.quarantine /absolute/path/to/downloaded-app
```

The attribute's presence or absence alone does not identify the cause. Do not remove it or disable Gatekeeper as a generic fix. Apple describes Gatekeeper's checks for downloaded software and its tracking of file provenance in [Gatekeeper and runtime protection](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web).

## Read-only first-pass check

[Mac Automation Doctor Free](../README.md) checks several common deterministic causes before you start editing or repeatedly reloading jobs:

- plist validity;
- missing executables;
- duplicate labels;
- missing working/log directories;
- relevant permission problems;
- local automation/runtime context.

**[Download Mac Automation Doctor Free](https://github.com/jgilles97-ctrl/mac-automation-doctor/releases/download/v1.0.0-free/mac-automation-doctor-free.zip)**

The diagnostic is local and read-only. It does not unload services, delete files, kill processes, or automatically rewrite your plist.

## Apple references

Apple’s current Terminal documentation describes `launchd` as the macOS mechanism for managing daemons and agents and `launchctl` as the command-line interface used to work with them. For app-bundled helpers on modern macOS, also review Apple’s Service Management documentation.
