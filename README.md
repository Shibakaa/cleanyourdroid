<div align="center">

# cleanyourdroid

**Your Android phone, minus the ads and spyware.**  
Debloat and optimize any Android device over ADB with your AI coding agent.

[English](README.md) &bull; [Русская версия](README.ru.md)

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-10b981.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20HyperOS%20%7C%20OneUI-38bdf8.svg?logo=android&logoColor=white)](https://developer.android.com)
[![Root](https://img.shields.io/badge/Root-Not%20Required%20(100%25%20Rootless)-emerald.svg)](#zero-blindness--safety-guarantee)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-indigo.svg)](https://github.com/Shibakaa/cleanyourdroid/pulls)
[![Flagship Tested](https://img.shields.io/badge/Tested-POCO%20F5%20(marble)-f43f5e.svg)](devices/xiaomi/poco-f5-marble.md)

</div>

---

Modern Android phones from Xiaomi, Samsung, BBK (OnePlus/Realme/Oppo), and even Google ship with an absurd amount of background telemetry daemons, lockscreen adware, partner bloatware, and silent APK installers.

`cleanyourdroid` turns your AI coding agent (Claude Code, Gemini CLI, Cursor, Windsurf, Codex) into a specialized Android systems engineer. Plug in your phone via USB or Wireless Debugging, paste `PROMPT.md`, and let the agent audit, debloat, restrict battery drains, and compile ART profiles &mdash; with zero root and instant 1-click reversibility.

The agent never decides from memory: a deterministic planner cross-references your installed packages against two curated databases, and every executed change is logged, so the report and the reversal script cannot drift from what actually ran.

---

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CLEANYOURDROID OPTIMIZATION REPORT                │
├────────────────────────────────────────────────────────────────────────┤
│ Device:           Xiaomi POCO F5 (marble)                              │
│ OS & Build:       Android 15 (HyperOS 3.0.2.0.VMRRUXM)                 │
│ Chipset / SoC:    Qualcomm Snapdragon 7+ Gen 2 (SM7475)                │
├────────────────────────────────────────────────────────────────────────┤
│ METRIC                    │ BEFORE       │ AFTER        │ DELTA        │
├───────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Enabled Packages          │ 731          │ 716          │ -15          │
│ Used RAM (PSS)            │ 6788.9 MB    │ 6133.0 MB    │ -655.9 MB    │
│ Available RAM             │ 4371.1 MB    │ 5027.0 MB    │ +655.9 MB    │
│ Free RAM (incl. cache)    │ 9305.8 MB    │ 9121.4 MB    │ -184.4 MB    │
├────────────────────────────────────────────────────────────────────────┤
│ Scope: user-0 packages + settings only; APKs stay in /system.          │
│ Available RAM gain: +655.9 MB (total minus used, dumpsys PSS).         │
│ Action log: 23 recorded, 23 reversible.                                │
│ Reversal: bash ./backups/restore.sh                                    │
└────────────────────────────────────────────────────────────────────────┘
```

> **Live Bento Report Preview:** Check out [`assets/sample-report.html`](assets/sample-report.html) for an interactive, self-contained dark-mode report generated directly from hardware telemetry.

---

## How It Works

| Stage | Action | Description |
|:---:|:---|:---|
| **1** | **Snapshot & backup** | `tools/audit.py snapshot before` records RAM, packages and top processes; settings and package lists are dumped to `backups/`. |
| **2** | **Deterministic plan** | `tools/plan.py` cross-references the installed packages against `safety/known_bloatware.json` and refuses anything in `safety/bootloop_blacklist.json`. The agent presents that table for approval instead of inventing package names. |
| **3** | **Execute & log** | Each approved change is executed and immediately recorded with `tools/audit.py log-action`, including its exact reverse command. |
| **4** | **Tune** | Standby buckets, AppOps, Private DNS, animation scales, cache trim and ART compilation &mdash; all optional, all previewed before they run, all logged. |
| **5** | **Report & reversal** | `compare` prints the summary card and writes `backups/report.html`; `restore-script` regenerates `backups/restore.sh` from the log. |

---

## Quick Start

### 1. Prerequisites
- A computer with **Python 3.10+** and **ADB** ([Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)). No pip install, no virtualenv: stdlib only (CI covers 3.10 and 3.13 on Linux and Windows).
- Any AI coding tool: [Claude Code](https://claude.ai/code), [Gemini CLI](https://github.com/google-gemini), [Cursor](https://cursor.sh), or [Windsurf](https://codeium.com/windsurf).

### 2. Enable Developer Options on Your Phone
Connect your phone via USB cable and configure Developer Options:

<details>
<summary><b>Xiaomi / POCO / Redmi (HyperOS & MIUI) &mdash; Important!</b></summary>

1. **Settings &rarr; About Phone** &rarr; tap **OS version** 7 times.
2. **Settings &rarr; Additional settings &rarr; Developer options**.
3. Enable **USB debugging**.
4. Enable **USB debugging (Security settings)**. *(Requires an active SIM card and signed-in Mi Account. If disabled, ADB commands will throw `SecurityException`).*
</details>

<details>
<summary><b>Samsung Galaxy (One UI)</b></summary>

1. **Settings &rarr; About phone &rarr; Software information** &rarr; tap **Build number** 7 times.
2. **Settings &rarr; Developer options** &rarr; toggle **USB debugging**.
</details>

<details>
<summary><b>Google Pixel / Motorola / Sony (AOSP / Pixel UI)</b></summary>

1. **Settings &rarr; About phone** &rarr; tap **Build number** 7 times.
2. **Settings &rarr; System &rarr; Developer options** &rarr; toggle **USB debugging**.
</details>

<details>
<summary><b>Realme / OnePlus / Oppo (ColorOS / OxygenOS)</b></summary>

1. **Settings &rarr; About device &rarr; Version** &rarr; tap **Version number** 7 times.
2. **Settings &rarr; Additional settings &rarr; Developer options** &rarr; toggle **USB debugging**.
3. Toggle **Disable permission monitoring** if package commands encounter prompts.
</details>

### 3. Run the Agent
Open this repository in your agent's terminal or editor workspace and paste the contents of [`PROMPT.md`](PROMPT.md):

```bash
# Example with Claude Code:
claude
# Now paste the contents of PROMPT.md
```

```bash
# Example with Gemini CLI:
gemini
# Now paste the contents of PROMPT.md
```

Sit back and review the proposed changes before approving.

### 4. Or just look at the plan (no agent, no risk)
```bash
python3 tools/plan.py            # what would be removed on *this* phone
python3 tools/plan.py --format md
python3 tools/plan.py --validate # sanity-check the databases
```
`plan.py` is read-only: it never touches the device.

---

## Zero-Blindness & Safety Guarantee

Unlike blind shell scripts that purge packages haphazardly:
1. **Deterministic guard:** `tools/plan.py` excludes everything listed in [`safety/bootloop_blacklist.json`](safety/bootloop_blacklist.json) before the agent ever sees a candidate, and prints how many protected packages are present as proof the guard is live. Essential components (`com.miui.securitycenter`, `com.xiaomi.finddevice`, `com.miui.powerkeeper`, Knox core, `SystemUI`, dialer, active IME/launcher) are strictly protected.
2. **No invented package names:** the only removal candidates are entries of [`safety/known_bloatware.json`](safety/known_bloatware.json) that are actually installed. Anything else requires explicit, identifier-verified approval.
3. **Zero data loss (`-k` flag):** system packages are uninstalled with `pm uninstall -k --user 0`. The APK remains in `/system` and the app data stays put.
4. **Verified execution:** every batch is checked with `pm list packages -e --user 0` and `dumpsys window` so a crash-looping SystemUI is caught immediately.
5. **Instant reversibility:** every change is recorded with its exact reverse command in `backups/actions.json`, and `backups/restore.sh` is generated from that log:
   ```bash
   # Restore everything, newest change first:
   bash ./backups/restore.sh
   # Target one device when several are attached:
   ADB="adb -s <serial>" bash ./backups/restore.sh
   ```

> [!NOTE]
> `pm uninstall -k --user 0` frees **RAM and background activity, not storage**: the APK stays in the system partition and `-k` keeps the data. Storage is reclaimed by `pm trim-caches` (caches only). The README used to imply otherwise; it no longer does.

---

## What Gets Cleaned

### 1. Ads, Trackers & Telemetry
- **Xiaomi / POCO:** `com.miui.msa.global` (MIUI System Ads), `com.miui.analytics`, `com.miui.bugreport`, `com.miui.Hybrid` (Quick Apps ad vector), `com.aura.oobe.xiaomi` (Digital Turbine / DT Ignite), `com.ironsource.aura.xiaomi`.
- **Samsung:** `com.samsung.android.app.spage` (Samsung Free ad feed), `com.samsung.android.rubin.app` (Customization Service telemetry).
- **Universal:** Meta/Facebook system hooks (`com.facebook.system`, `com.facebook.appmanager`, `com.facebook.services`).

### 2. OEM Bloatware & Spyware Browsers
- `com.miui.android.fashiongallery` (Lockscreen Wallpaper Carousel ads)
- `com.mi.globalbrowser` (Mi Browser telemetry suite)
- `com.xiaomi.glgm` (Game Center promotional spam)
- `com.miui.yellowpage` (Caller ID advertiser service)
- `com.miui.videoplayer` & `com.miui.player` (Ad-filled media stores)
- `com.xiaomi.mipicks` (GetApps silent installer)
- `com.samsung.android.bixby.agent` (Bixby voice wake-up service)

### 3. Google Pixel / AOSP
There is no OEM ad SDK to remove here. The `google_pixel` category lists preinstalled apps that need a decision: Pixel Tips (safe to drop), YouTube / YouTube Music / Photos / Chrome / Gemini / Digital Wellbeing / Personal Safety (your call). Google's own telemetry stack (`com.google.android.gms`, `com.google.android.gsf`) is **not** removable without root, and this tool will not pretend otherwise.

### 4. Background Memory Optimization
- Restricts heavy third-party apps with App Standby buckets (`am set-standby-bucket <pkg> restricted`) and, when you ask for it, AppOps (`cmd appops set <pkg> RUN_IN_BACKGROUND ignore` &mdash; this *can* silence notifications).
- Trims package caches: `pm trim-caches 999G`.
- Triggers profile-guided AOT compilation: `cmd package bg-dexopt-job`, or `cmd package compile -m speed-profile -f <pkg>` for individual apps.

---

## Device & OS Compatibility Matrix

> [!IMPORTANT]
> Package namespaces, background services, and AppOps permissions vary across OEM skins and major Android releases. **Only configurations marked `✅ Verified` have been tested on real physical hardware with complete before/after telemetry logs.**
> For configurations marked `⚠️ Untested`, the agent operates conservatively using `safety/bootloop_blacklist.json` and interactive user confirmation. We actively encourage community submissions to expand verified profiles!

| Brand / OEM | Model Family | Codename | OS & Android Version | Test Status | Profile & Benchmarks |
|:---|:---|:---|:---|:---:|:---:|
| **Xiaomi / POCO** | **POCO F5 / Redmi Note 12 Turbo** | `marble` / `marblein` | **HyperOS 3.0** (Android 15) & **HyperOS 1.0** (Android 14) | ✅ **Verified** | [View Hardware Profile](devices/xiaomi/poco-f5-marble.md) |
| **Samsung** | Galaxy S23 / S24 Series | `kalama` / `pineapple` | One UI 6.x / 7.x (Android 14 / 15) | ⚠️ **Untested** | *Community PR Welcome* |
| **OnePlus** | OnePlus 11 / 12 | `salami` / `pineapple` | OxygenOS 14 / 15 (Android 14 / 15) | ⚠️ **Untested** | *Community PR Welcome* |
| **Google** | Pixel 7 / 8 / 9 / 10 Series | `panther` / `shiba` / `caiman` | Pixel UI (Android 14 - 16) | ⚠️ **Untested** | *No OEM ads: expect 1-2 safe removals* |
| **Realme / Oppo** | GT / Find Series | Various | ColorOS 14 (Android 14) | ⚠️ **Untested** | *Community PR Welcome* |

### Add Your Device Profile
Debloated your phone with `cleanyourdroid`? Submit a Pull Request with your device profile under `devices/<brand>/<codename>.md` so other users can optimize their devices safely!

---

## FAQ

**"What would it remove on my phone?"**
Run `python3 tools/plan.py`. It prints exactly that, grouped by risk, using the databases in `safety/`. On a Pixel 10 Pro XL the honest answer is: *Pixel Tips, plus a decision list of preinstalled Google apps* &mdash; there is no MSA, no Digital Turbine, and no Meta installer on a Pixel. The repo's Pixel data is illustrative, not a verified profile; a PR from a real device is very welcome.

**"Why does one number go down after a cleanup?"**
`Free RAM` from `dumpsys` includes cached pages, so it fluctuates with cache pressure. `Available RAM` (total minus used) is the number that reflects headroom. Both are printed so you can check the arithmetic yourself.

**"Does this void my warranty / trip Knox / break OTA?"**
No root, no bootloader unlock, no system modification: packages are only hidden from user 0 and settings are changed through the official `settings` provider. A factory reset restores everything, and `restore.sh` does it without one.

---

## Repository Structure

```
cleanyourdroid/
├── AGENTS.md                  # Master instructions for AI coding assistants
├── CLAUDE.md                  # Claude Code entry point (points at AGENTS.md)
├── GEMINI.md                  # Gemini CLI entry point (points at AGENTS.md)
├── PROMPT.md                  # 5-stage interactive user prompt
├── CONTRIBUTING.md            # Database rules, device profiles, house rules
├── README.md                  # English documentation
├── README.ru.md               # Russian documentation
├── safety/
│   ├── bootloop_blacklist.json # Hard-blocked packages plus wildcard families
│   └── known_bloatware.json    # Curated database of verified bloatware
├── tools/
│   ├── adbkit.py              # Shared ADB plumbing (device selection, errors)
│   ├── audit.py               # Snapshots, action log, reversal script, HTML report
│   ├── plan.py                # Deterministic package plan against both databases
│   └── tune.py                # Rootless tuning: standby, AppOps, DNS, scales
├── tests/
│   ├── fake_adb.py            # Stand-in adb, so tests run without a phone
│   └── test_tools.py          # End-to-end tests (python -m unittest discover -s tests)
└── devices/
    ├── _template.md           # Device profile template for PRs
    └── xiaomi/
        └── poco-f5-marble.md  # Reference device benchmark & config
```

---

## Tooling

### `tools/plan.py` &mdash; what would be removed?
```bash
python3 tools/plan.py                 # human-readable groups
python3 tools/plan.py --format md     # Markdown table for the chat / a PR
python3 tools/plan.py --format json   # structured, for scripts and agents
python3 tools/plan.py --validate      # duplicate / overlap check for the databases
python3 tools/plan.py --packages-file backups/installed_packages_before.txt  # offline
```

### `tools/audit.py` &mdash; telemetry, action log, report
```bash
python3 tools/audit.py snapshot before
python3 tools/audit.py log-action --kind package --target com.miui.msa.global \
  --command "adb shell pm uninstall -k --user 0 com.miui.msa.global" \
  --restore "adb shell cmd package install-existing com.miui.msa.global" --result ok
python3 tools/audit.py snapshot after
python3 tools/audit.py restore-script     # regenerate backups/restore.sh from the log
python3 tools/audit.py compare before after
```

The resulting `./backups/report.html` is an interactive dark-mode bento dashboard that only claims what was measured or logged.

### `tools/tune.py` &mdash; the part that is not about packages
```bash
python3 tools/tune.py list                  # every tweak, what it changes, what it costs
python3 tools/tune.py status                # current values on the phone
python3 tools/tune.py apply --id animations --id private_dns            # dry run
python3 tools/tune.py apply --id animations --id private_dns --yes      # execute + log
python3 tools/tune.py apply --id standby --package com.facebook.katana --yes
python3 tools/tune.py revert --id private_dns --yes
```
Available tweaks: animation scales, Private DNS ad blocking, background Wi-Fi/Bluetooth scanning, the phantom-process killer, and per-app standby bucket / AppOps restrictions. Every tweak states its risk, prints the exact command, verifies the read-back value, and lands in `backups/actions.json` so `restore.sh` undoes it too.

### Running the tests
```bash
python -m unittest discover -s tests -v
```
No phone required: `tests/fake_adb.py` answers `getprop`, `dumpsys meminfo` and `pm list packages`. Point the tools at any other adb wrapper with `CLEANYOURDROID_ADB`.

---

## License

Released under the [MIT License](LICENSE). Built for the open-source community.  
*Inspired by [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).*
