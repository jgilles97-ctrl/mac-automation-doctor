# Why launchd Cannot Find a Command That Works in Terminal

One of the most common macOS automation failures is simple to describe:

> The command works when I type it in Terminal, but my LaunchAgent says it cannot find it.

The usual reason is that **your interactive shell environment and launchd's environment are not the same thing**.

## Terminal may be doing more work than you realize

When Terminal starts a shell, shell startup files and developer tooling may modify `PATH` or define aliases, functions, and environment variables. Tools installed through Homebrew, a language version manager, or a user-local package directory may therefore resolve automatically in Terminal.

A LaunchAgent should not be assumed to load that same interactive shell configuration.

## Find the real executable path

In Terminal, check the command you are relying on:

```bash
which python3
which node
which ruby
which git
```

You can also inspect all matches in your current shell:

```bash
type -a python3
```

Then compare the actual executable path with the first value in your LaunchAgent's `ProgramArguments` array.

## Prefer explicit paths for automation dependencies

For a deterministic background job, an explicit executable path is usually easier to reason about than relying on whichever `PATH` happens to exist.

For example, if a script requires a specific Python or Node installation, point the LaunchAgent at the intended interpreter rather than assuming `python3` or `node` will resolve exactly as it does in your interactive shell.

## Shell features are not automatic

`ProgramArguments` is an array of the program and its arguments. It is not automatically a Terminal command line.

Do not assume launchd will automatically interpret:

- pipes such as `|`;
- redirects such as `>`;
- shell aliases;
- wildcards;
- shell functions;
- `$HOME` or other shell expansion;
- command substitution.

If a job genuinely needs shell syntax, invoke a shell deliberately and understand the quoting and environment you are creating.

## Check the script's own assumptions

Even when the interpreter path is correct, the script may depend on:

- a current working directory;
- relative file paths;
- environment variables;
- package-manager shims;
- configuration files loaded only by an interactive shell;
- permissions that differ in the background context.

Try to make background automation use explicit paths for important files and dependencies.

## Check output paths too

A LaunchAgent may appear to do nothing when the job actually starts but cannot create its stdout/stderr file or access the configured directory. Verify those paths exist and are writable.

## Use a read-only diagnostic pass

[Mac Automation Doctor Free](../README.md) checks common LaunchAgent failure points including missing executables, plist validity, directories, permissions, duplicate labels, and related local automation context.

**[Download Mac Automation Doctor Free](https://github.com/jgilles97-ctrl/mac-automation-doctor/releases/download/v1.0.0-free/mac-automation-doctor-free.zip)**

It runs locally and makes no automatic repairs, so you can narrow the likely cause before changing the automation.

## Apple reference

Apple documents `launchd` as the macOS service used to manage agents and daemons. Apple’s launchd documentation also defines `ProgramArguments` as the tokenized program/argument array. Verify the current documentation for the macOS version and helper architecture you are using.