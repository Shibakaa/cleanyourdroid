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
│ Active Used RAM           │ 6,788.9 MB   │ 6,133.0 MB   │ -655.9 MB    │
│ Available Memory Buffer   │ 9,305.8 MB   │ 9,121.4 MB   │ -184.4 MB    │
├────────────────────────────────────────────────────────────────────────┤
│ Status: 100% Rootless Clean & Optimized                                │
│ Active RAM Gain: +655.9 MB freed from background services              │
│ Reversibility: Ready via ./backups/restore.sh                          │
└────────────────────────────────────────────────────────────────────────┘
```

> **Live Bento Report Preview:** Check out [`assets/sample-report.html`](assets/sample-report.html) for an interactive, self-contained dark-mode report generated directly from hardware telemetry.

---

## How It Works

| Stage | Action | Description |
|:---:|:---|:---|
| **1** | **Backup & Snapshot** | Takes baseline memory and package snapshot via `tools/audit.py`, records system settings, and creates `restore.sh`. |
| **2** | **Interactive Audit** | Cross-references installed packages against `safety/known_bloatware.json` and `safety/bootloop_blacklist.json`, presenting a categorized table for approval. |
| **3** | **Debloat & ART Compile** | Disables/uninstalls approved bloat (`-k` data retained), applies `appops` background restrictions, trims cache, and runs `cmd package bg-dexopt-job`. |
| **4** | **Benchmark Report** | Generates a terminal summary card and an interactive dark-mode HTML bento report at `./backups/report.html`. |

---

## Quick Start

### 1. Prerequisites
- A computer with **Python 3.8+** and **ADB** ([Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)).
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

---

## Zero-Blindness & Safety Guarantee

Unlike blind shell scripts that purge packages haphazardly:
1. **Never Brick Guarantee:** Every package removal candidate is verified against [`safety/bootloop_blacklist.json`](safety/bootloop_blacklist.json). Essential components (`com.miui.securitycenter`, `com.xiaomi.finddevice`, `com.miui.powerkeeper`, Knox core, `SystemUI`, dialers, and input methods) are strictly protected.
2. **Zero Data Loss (`-k` Flag):** System packages are uninstalled using `pm uninstall -k --user 0`. The APK remains in `/system` and user app data/cache remains intact.
3. **Instant Reversibility:** Every single package and setting modification generates an exact reversal command in `./backups/restore.sh`:
   ```bash
   # Restore all packages at any time:
   bash ./backups/restore.sh
   ```

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

### 3. Background Memory Optimization
- Restricts rogue third-party apps holding persistent wake-locks via `adb shell cmd appops set <pkg> RUN_IN_BACKGROUND ignore`.
- Trims OS package caches: `adb shell pm trim-caches 999G`.
- Triggers profile-guided Ahead-of-Time ART compilation on remaining system packages: `adb shell cmd package bg-dexopt-job`.

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
| **Google** | Pixel 7 / 8 / 9 Series | `panther` / `shiba` / `caiman` | Pixel UI (Android 14 / 15) | ⚠️ **Untested** | *Community PR Welcome* |
| **Realme / Oppo** | GT / Find Series | Various | ColorOS 14 (Android 14) | ⚠️ **Untested** | *Community PR Welcome* |

### Add Your Device Profile
Debloated your phone with `cleanyourdroid`? Submit a Pull Request with your device profile under `devices/<brand>/<codename>.md` so other users can optimize their devices safely!

---

## Repository Structure

```
cleanyourdroid/
├── AGENTS.md                  # Master instructions for AI coding assistants
├── GEMINI.md                  # Gemini-specific agent copy
├── CLAUDE.md                  # Claude Code-specific agent copy
├── PROMPT.md                  # 4-stage interactive user prompt
├── README.md                  # English documentation
├── README.ru.md               # Russian documentation
├── safety/
│   ├── bootloop_blacklist.json # Hard-blocked critical system packages
│   └── known_bloatware.json    # Curated database of verified bloatware
├── tools/
│   └── audit.py               # Zero-dependency audit & HTML bento generator
└── devices/
    └── xiaomi/
        └── poco-f5-marble.md  # Reference device benchmark & config
```

---

## Telemetry & Benchmarking Tool (`audit.py`)

You can also use the bundled zero-dependency Python tool standalone:

```bash
# Capture baseline before debloating:
python3 tools/audit.py snapshot before

# Capture status after debloating:
python3 tools/audit.py snapshot after

# Compare snapshots, print terminal summary, and generate HTML bento report:
python3 tools/audit.py compare before after
```

The resulting `./backups/report.html` is an interactive dark-mode bento dashboard ready for sharing on Reddit or X.

---

## License

Released under the [MIT License](LICENSE). Built for the open-source community.  
*Inspired by [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).*
