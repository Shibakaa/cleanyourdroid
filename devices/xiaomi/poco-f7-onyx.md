# POCO F7 (`onyx`) &bull; Xiaomi HyperOS 3.0 profile

Verified rootless debloat session on a global EEA unit, 2026-11-07. Package identifiers and outcomes below were read from the device, not guessed.

---

## 1. Device metadata

| Parameter | Specification |
|:---|:---|
| **Commercial model** | POCO F7 (`25053PC47G`) |
| **Device codename** | `onyx` (product `onyx_eea`) |
| **System on Chip** | Qualcomm `SM8735` (Snapdragon 8s Gen 4) |
| **Memory / storage** | 12 GB LPDDR5X / 512 GB UFS (`/data` 479 GB usable) |
| **Display** | 6.83" AMOLED, 1280 &times; 2772, 120 Hz |
| **Verified OS build** | HyperOS 3.0 `OS3.0.301.0.WOLEUXM`<br>Android 16 `BP2A.250605.031.A3`<br>Security patch `2026-05-01` |
| **Target architecture** | `arm64-v8a` |

---

## 2. Prerequisites

1. **USB debugging** = ON.
2. **USB debugging (Security settings)** = ON. This writes `persist.security.adbinput=1` and requires a logged-in Mi Account plus a SIM.
3. **Reboot once after enabling it.** On this unit the property read `1` immediately but `input keyevent` kept throwing `INJECT_EVENTS` until the phone was rebooted. After the reboot, input injection worked.
4. Wireless Debugging: pair once; the connect port changes on every reboot, so the serial in `restore.sh` must be updated after a restart.

> [!IMPORTANT]
> **`pm disable-user` is refused for system packages even with the security toggle ON and after a reboot.** It throws:
> `java.lang.SecurityException: Cannot disable system packages` (PackageManagerServiceImpl.shouldRestrictEnabledSettingsChange).
> The working rootless method on this build is `pm uninstall -k --user 0` (APK stays in `/system` or `/product`, data kept, reversible with `cmd package install-existing`). This is the AGENTS.md Tier 2 fallback, not a permanent uninstall.
>
> A package that is **not** flagged as system (`pm list packages -s` does not list it) *can* still be disabled normally with `pm disable-user` — that was the case for `cn.wps.xiaomi.abroad.lite` despite its `/product/data-app` path.

---

## 3. Verified removals

All nine were confirmed gone from `pm list packages -e --user 0` and still present in `pm list packages -u --user 0`. None was reverted.

| Package | App name | Method | Why it is safe here | Reverted? |
|:---|:---|:---|:---|:---:|
| `com.miui.analytics` | MIUI Analytics | `pm uninstall -k --user 0` | Telemetry only; no UI dependency. | no |
| `com.miui.bugreport` | MIUI Bug Report / Feedback | `pm uninstall -k --user 0` | Crash-log uploader; Settings > Feedback loses its backend. | no |
| `com.miui.msa.global` | MIUI System Ads (MSA) | `pm uninstall -k --user 0` | Ad delivery service; no system dependency. | no |
| `com.google.android.videos` | Google TV / Play Movies stub | `pm uninstall -k --user 0` | Storefront stub; nothing else references it. | no |
| `com.mi.globalbrowser` | Mi Browser Pro | `pm uninstall -k --user 0` | Chrome is the default browser on this unit. | no |
| `com.miui.yellowpage` | Yellow Pages / caller ID | `pm uninstall -k --user 0` | Business-directory lookup; calls and SMS unaffected. | no |
| `com.miui.player` | Mi Music | `pm uninstall -k --user 0` | No default music handler; YouTube Music / Podcast Addict remain. | no |
| `com.miui.videoplayer` | Mi Video | `pm uninstall -k --user 0` | Gallery Go can open local video; install VLC for a full player. | no |
| `cn.wps.xiaomi.abroad.lite` | WPS Office (Xiaomi preinstall) | `pm disable-user --user 0` | Not system-flagged; no launcher activity (no home icon). | no |

---

## 4. Restrictions instead of removal

None applied. No `appops` or standby-bucket changes were made.

---

## 5. Packages kept for stability

| Package | What breaks / risk |
|:---|:---|
| `com.miui.securitycenter` | Immediate bootloop; HyperOS permission engine. Never touch. |
| `com.xiaomi.finddevice` | TrustZone-validated on boot; bootloop on next restart. |
| `com.miui.powerkeeper` | Locks display at 60 Hz and breaks thermal management. |
| `com.xiaomi.xmsf` | Breaks Xiaomi push notifications and account auth. |
| `com.mi.android.globallauncher` | Home screen and gesture navigation (active launcher). |
| `com.android.systemui` | Status bar / lock screen. |
| `com.miui.systemui.carriers.overlay` | HyperOS status-bar overlay; SystemUI crashes if disabled. |
| `com.miui.guardprovider`, `com.miui.securityadd` | Bound to Security Center. |
| `com.xiaomi.account` | Device activation and account auth. |
| `com.miui.core` | Shared HyperOS resources; bootloop. |
| `com.miui.miservice` | Present and left untouched: the gist lists it as commonly removed, but it is **not** in `safety/known_bloatware.json`, so it needs explicit per-package approval. |
| `com.xiaomi.joyose` | Left untouched: removing it is a performance/thermal trade-off (`optional_with_tradeoff`). |

---

## 6. Measurements

| Metric | Before | After | Delta |
|:---|:---:|:---:|:---:|
| Enabled packages (user 0) | 530 | 521 | **-9** |
| Used RAM (dumpsys PSS) | 10511.7 MB | 6059.0 MB | -4452.7 MB * |
| Available RAM (total − used) | 722.0 MB | 5174.7 MB | +4452.7 MB * |
| Free RAM incl. cache (dumpsys) | 5213.4 MB | 8536.1 MB | +3322.7 MB * |

> [!NOTE]
> **Only the `-9` packages are attributable to this session.** The `before` snapshot was taken while the phone was in active use; the `after` snapshot was taken after a reboot and while the screen was locked/idle. The RAM deltas are therefore dominated by the reboot, not by the removals, and must not be published as a debloat gain. No `pm trim-caches` and no `bg-dexopt-job` were run, so there is no storage claim either.

Snapshots: `backups/before.json`, `backups/after.json`; action log: `backups/actions.json`.

---

## 7. Notes

- No crash, bootloop or launcher/SystemUI restart was observed after the removals. SystemUI and `com.mi.android.globallauncher` stayed alive, and the phone locked/unlocked normally.
- All five launcher pages were inventoried before the changes. None of the nine packages was on the home screen; WPS has no launcher activity at all, and the Mi Browser / Mi Music / Mi Video icons lived only in the app drawer.
- Conflicts handled during the session:
  - `com.miui.securitycenter`: repo says bootloop (never touch); the gist leaves a cautious door open. The repo was followed.
  - `com.miui.miservice`: gist recommends removing; the repo database does not list it. Not touched.
  - `com.google.android.apps.wellbeing`: gist marks it safe; the repo marks it `user_discretion`. Left untouched.
- Reversal: `bash backups/restore.sh` (replace the stale ADB serial after a reboot), or per package:
  - `adb shell pm enable cn.wps.xiaomi.abroad.lite`
  - `adb shell cmd package install-existing <package>` for the other eight.
- Session date: 2026-11-07. Session summary: `Debloat_PocoF7_resumo.md` (workspace root).
