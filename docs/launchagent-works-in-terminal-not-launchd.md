# LaunchAgent Works in Terminal but Not in launchd: A Practical Checklist

If a script works when you run it in Terminal but fails as a macOS LaunchAgent, the problem is often **not the script itself**. The environment, executable path, working directory, permissions, or plist configuration may be different when `launchd` starts it.

Apple documents `launchd` as the supported macOS mechanism for managing agents and daemons. User LaunchAgents commonly live in `~/Library/LaunchAgents`.

## 1. Check the executable path

Do not assume `launchd` can find the same command that your interactive shell finds.

If your plist contains `ProgramArguments`, the first item should identify the executable you expect to run. Prefer a real absolute path when practical rather than depending on shell aliases, shell startup files, or an interactive PATH.

Useful checks in Terminal:

```bash
which python3
which node
which bash
which zsh
```

Then compare those paths with the executable referenced by the plist.

## 2. Remember that your shell setup is not the launchd environment

Terminal may load shell configuration that adds Homebrew, language runtimes, package-manager shims, aliases, or other directories to `PATH`. A LaunchAgent does not automatically reproduce your interactive Terminal environment.

If a script depends on tools installed by Homebrew, Python, Node, Ruby, or a version manager, confirm the exact executable path instead of assuming it will resolve the same way.

## 3. Validate the plist

A malformed property list can prevent the job from loading correctly.

```bash
plutil -lint ~/Library/LaunchAgents/com.example.job.plist
```

A valid XML plist is necessary, but it does not prove that every referenced executable or directory actually exists.

## 4. Check Label and ProgramArguments

A launchd job should have a unique `Label`. Apple’s launchd documentation also describes `ProgramArguments` as the tokenized program and argument array.

Common mistakes include:

- duplicate labels;
- wrong executable path;
- accidentally putting a whole shell command into one argument when a shell was not explicitly invoked;
- assuming shell expansion such as `$HOME`, wildcards, aliases, or pipes will happen automatically.

If you need shell syntax, call the shell explicitly and understand the quoting involved.

## 5. Check working, output, and log paths

If the plist references a working directory, stdout file, stderr file, or another directory, make sure it actually exists and is writable by the user running the LaunchAgent.

A job can fail before useful logging appears if the configured output directory itself is missing or inaccessible.

## 6. Check file permissions

Verify that the executable or script can actually run:

```bash
ls -l /path/to/script
```

If it is meant to execute directly, confirm it has the appropriate executable permission and a valid interpreter/shebang where required.

## 7. Confirm you are using the right launchd domain

A LaunchAgent runs in a user context, while a LaunchDaemon is system-level. Do not troubleshoot them as if they are interchangeable.

For a user LaunchAgent, confirm you are working with the intended logged-in user and the correct plist location.

## 8. Look at the actual job state

Use `launchctl` to inspect what launchd currently knows about the job rather than assuming the plist on disk is loaded exactly as expected.

The exact command depends on the launchd domain and job label. Avoid repeatedly unloading/reloading a job without first confirming its current state and the underlying configuration problem.

## 9. Check macOS background-item and app-helper behavior

Modern macOS also has Service Management and background-item behavior for app-bundled helpers. A legacy standalone LaunchAgent is not the same thing as an app-managed helper registered through modern Service Management APIs.

If the automation belongs to an installed app, review the app’s supported setup before manually editing its helper configuration.

## Faster first-pass diagnosis

[Mac Automation Doctor Free](../README.md) performs a local, read-only pass over several of these deterministic failure points, including plist validity, missing executables, duplicate labels, directories, permissions, and related automation context.

**[Download the free release](https://github.com/jgilles97-ctrl/mac-automation-doctor/releases/download/v1.0.0-free/mac-automation-doctor-free.zip)**

It makes no automatic repairs, requires no cloud AI service for diagnostic decisions, and is designed to help you narrow the problem before changing the Mac.

## Apple references

- Apple Terminal User Guide: Script management with launchd in Terminal on Mac
- Apple Developer: Service Management
- Apple Developer archive: Creating Launch Daemons and Agents

Always verify current Apple documentation for the macOS version you are targeting.