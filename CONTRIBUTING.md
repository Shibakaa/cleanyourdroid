# Contributing

Thanks for taking the time. This project touches other people's phones, so the bar is "safe and reversible" rather than "fast".

## Before you open a PR

```bash
python -m unittest discover -s tests -v   # 17 tests, no phone required
python tools/plan.py --validate           # database integrity
```

Both run in CI on Python 3.8 and 3.12, Windows and Linux.

## What we need most

**1. Device profiles** (`devices/<brand>/<codename>.md`).
Copy [`devices/_template.md`](devices/_template.md) and fill it with a real session: codename, build id, SoC, the exact packages you removed or restricted, before/after numbers, and anything that misbehaved afterwards — including what you reverted. An untested profile is worse than no profile.

**2. Database fixes** (`safety/known_bloatware.json`).
An entry needs all of: `package`, `name`, `oem`, `category`, `recommendation`, `description`, `impact`.
- `recommendation` is one of `safe_removal`, `user_discretion`, `optional_with_tradeoff`.
- `safe_removal` means: tested, nothing breaks, no user-facing feature is lost. If in doubt, use `user_discretion`.
- One package per entry, exact identifier, no wildcards here — wildcards belong in `safety/bootloop_blacklist.json`.

**3. Blacklist additions** (`safety/bootloop_blacklist.json`).
Either a `package` entry with `risk_level` (`BOOTLOOP` / `CRITICAL_BREAKAGE`) and a `reason` explaining what breaks, or a `pattern` for a whole family (`com.google.android.gms.*`).
A pattern must **not** match anything in `known_bloatware.json`: `plan.py --validate` fails the build if it does.

**4. Tools and tests** (`tools/`, `tests/`).
`tests/fake_adb.py` emulates a device, so new behaviour should come with a test that needs no hardware. If you add a command the tools issue, teach the fake about it.

## House rules

- **Rootless only.** No `su`, no bootloader unlocking, no writing to `/system`.
- **Reversible by construction.** Every change must be recorded through `tools/audit.py log-action` (or `tools/tune.py`) with an exact reverse command. A feature that cannot be undone does not go in.
- **No invented package names.** Candidates come from the databases, never from memory.
- **Honest numbers.** If a metric is ambiguous (hello, dumpsys "Free RAM" that includes cache), label it instead of picking the flattering interpretation.
- **Conventional commits**, one concern per commit: `feat(tools):`, `fix(safety):`, `docs:`, `test:`.

## Reporting a bad removal

Open an issue with the device, the package, the symptoms, and whether `bash backups/restore.sh` fixed it. That report is how the blacklist grows.
