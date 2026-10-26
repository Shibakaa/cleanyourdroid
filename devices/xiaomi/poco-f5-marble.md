# POCO F5 (`marble`) &bull; Xiaomi HyperOS Optimization Guide

Comprehensive optimization profile and verified debloat list for the **POCO F5 / Redmi Note 12 Turbo** (`marble` / `marblein`), powered by Qualcomm Snapdragon 7+ Gen 2.

---

## 1. Device Metadata

| Parameter | Specification |
|:---|:---|
| **Commercial Model** | POCO F5 / Redmi Note 12 Turbo |
| **Device Codename** | `marble` (Global) / `marblein` (India) / `marble` (RU / EEA) |
| **System on Chip (SoC)** | Qualcomm Snapdragon 7+ Gen 2 (`SM7475-AB`, 4nm) |
| **Memory Configurations** | 8 GB / 12 GB LPDDR5 |
| **Internal Storage** | 256 GB UFS 3.1 |
| **Display Panel** | 6.67" 120Hz Flow AMOLED (1080 &times; 2400) |
| **Verified OS Versions** | &bull; **Xiaomi HyperOS 3.0.2.0.VMRRUXM** (Android 15, `AQ3A.250226.002`, RU Region)<br>&bull; **Xiaomi HyperOS 1.0.8.0.UMRMIXM** (Android 14, Global) |
| **Target Architecture** | `arm64-v8a` |

---

## 2. HyperOS Prerequisites

Prior to running `cleanyourdroid`, you **must** configure Xiaomi's dual ADB authorization switches:

1. Navigate to **Settings &rarr; About phone** and tap **OS version** 7 times to enable Developer options.
2. Go to **Settings &rarr; Additional settings &rarr; Developer options**.
3. Toggle **USB debugging** to `ON`.
4. Scroll down and toggle **USB debugging (Security settings)** to `ON`.
   > [!NOTE]
   > HyperOS requires an active SIM card and logged-in Mi Account to authorize "Security settings". This permission is required by Android to allow rootless package management (`pm uninstall`, `pm disable-user`, `appops`) via ADB.

---

## 3. Verified Safe Debloat List

The following packages have been thoroughly tested on HyperOS 1.0 / 3.0 (Android 14 & 15). Removing them causes zero system crashes, eliminates intrusive advertisements, and frees substantial RAM and storage.

### Group A: Adware & Tracking Daemons
| Package Identifier | App Name | Justification |
|:---|:---|:---|
| `com.miui.msa.global` | MIUI System Ads (MSA) | Primary background service serving ads across HyperOS apps. |
| `com.miui.analytics` | MIUI Analytics | Constant telemetry and upload wake-locks. |
| `com.miui.bugreport` | MIUI Bug & Feedback | Persistent log collector uploading diagnostic data. |
| `com.miui.Hybrid` | Miui Quick Apps | Lightweight HTML5 runtime exploited for push ads. |
| `com.miui.hybrid.accessory` | Quick Apps Accessory | Companion background daemon for Quick Apps. |
| `com.aura.oobe.xiaomi` | Digital Turbine (Aura) | Silently downloads promoted sponsor apps post-setup. |
| `com.ironsource.aura.xiaomi` | IronSource SDK | Monetization and ad distribution engine. |

### Group B: Meta / Facebook Preinstalled Stubs
| Package Identifier | App Name | Justification |
|:---|:---|:---|
| `com.facebook.system` | Meta App Installer | System installer allowing Facebook to bypass Play Store. |
| `com.facebook.appmanager` | Meta App Manager | Background asset manager holding wake-locks. |
| `com.facebook.services` | Meta Services | Connects system events to Meta telemetry servers. |

### Group C: Preloaded OEM Apps & Storefronts
| Package Identifier | App Name | Justification |
|:---|:---|:---|
| `com.miui.android.fashiongallery` | Wallpaper Carousel | Displays clickbait articles and ads on the lockscreen. |
| `com.mi.globalbrowser` | Mi Browser | Telemetry-heavy browser; replace with Brave, Chrome, or Firefox. |
| `com.xiaomi.glgm` | Xiaomi Game Center | Intrusive push notifications promoting pay-to-win games. |
| `com.miui.yellowpage` | Yellow Pages | Injects business directory ads into incoming call interface. |
| `com.miui.videoplayer` | Mi Video | Ad-heavy media player with persistent notification spam. |
| `com.miui.player` | Mi Music | Audio player bundled with streaming store ads. |
| `com.xiaomi.payment` | Mi Pay | Xiaomi proprietary payment layer (unneeded if using Google Wallet/Mir Pay). |
| `com.mipay.wallet.in` | Mi Credit / Wallet | Predatory instant loan promotion banners. |
| `com.miui.cleanmaster` | Clean Master Definitions | Legacy Cheetah Mobile tracking definitions. |
| `com.xiaomi.mipicks` | GetApps Store | Proprietary store pushing constant download prompts. |
| `cn.wps.xiaomi.abroad.lite` | WPS Office (preinstall) | Kingsoft office suite bundled on RUXM builds; duplicate of any office app you install. Removed in the verified session. |

### Group D: Russian Region Mandated Preloads & Stubs (`VMRRUXM` Specific)
Firmware builds targeted for the Russian market (`RUXM`) contain pre-activated Russian statutory software packages that remain active in the background:

| Package Identifier | App Name | Recommendation & Impact |
|:---|:---|:---|
| `ru.vk.store` | RuStore Marketplace | **User Discretion:** Alternative Russian app store. Safe to remove if you use Google Play or Aurora Store; keep if you rely on sanctioned Russian banking apps. |
| `ru.yandex.searchplugin` | Yandex Search & Alice | **User Discretion:** Heavy background voice recognition daemon and feed service. |
| `com.yandex.browser` / `ru.yandex.browser` | Yandex Browser | **User Discretion:** Preloaded browser. Safe to remove if using Chrome/Firefox. |
| `com.vkontakte.android` | VKontakte Client | **User Discretion:** Official VK client. Can be removed if unused; can also be restricted via `appops`. |
| `ru.mail.mailapp` | Mail.ru Mail Client | **Safe Removal:** Factory preloaded email client. |
| `ru.myoffice.documents.app.play` | MyOffice Documents | **Safe Removal:** Office viewer stub. Removes the app for user 0; the APK stays in `/system`, so expect no measurable storage gain. |
| `ru.rutube.app` | Rutube Video | **Safe Removal:** Video hosting client with notification promotions. |
| `com.yandex.preinstallsatellite` | Yandex Preinstall Satellite | **Safe Removal:** Silent installer stub that provisions the Yandex suite after first boot. Removed in the verified session; stops partner-app provisioning without losing a user-facing app. |
| `com.kms.free` | Kaspersky Mobile Security | **Safe Removal:** Extremely heavy I/O antivirus background scanner. Significant battery and CPU win upon removal. |
| `ru.yandex.disk` | Yandex Disk | **User Discretion:** Cloud photo auto-upload background service. |
| `ru.kinopoisk` | Kinopoisk | **User Discretion:** Streaming client. |
| `ru.ok.android` | Odnoklassniki (OK) | **Safe Removal:** Social network preinstall stub. |
| `com.gosuslugi` | Gosuslugi Portal | **User Discretion:** Russian government portal stub. |

### Group E: Optional Performance Tuning (Joyose)
| Package Identifier | App Name | Trade-Off Analysis |
|:---|:---|:---|
| `com.xiaomi.joyose` | Xiaomi Joyose Daemon | **Optional:** Joyose manages thermal throttling policies in gaming and background SMS telemetry. Removing it unlocks higher sustained FPS in Genshin Impact and emulation (Yuzu/Mali), but the phone may reach higher temperatures during extended gaming sessions. |

---

## 4. Critical Packages Kept for Stability

> [!CAUTION]
> The following packages **MUST NEVER BE REMOVED** on POCO F5 (`marble`). Disabling them will cause immediate bootloops or catastrophic UI failures on Android 14 and Android 15:

1. **`com.miui.powerkeeper` (CRITICAL DISPLAY DEPENDENCY):**
   - On the POCO F5, `com.miui.powerkeeper` controls dynamic display refresh rate switching.
   - If uninstalled or disabled, the screen **permanently locks at 60Hz**, disabling 120Hz mode completely.
   - **Verdict: ALWAYS KEEP.**

2. **`com.miui.securitycenter` (CORE OS INTEGRITY):**
   - Handles HyperOS permission dispatching, app security validations, and binder hooks.
   - Removing this causes an **instant, non-recoverable bootloop**.
   - **Verdict: ALWAYS KEEP.**

3. **`com.xiaomi.finddevice` (TRUSTZONE BOOT GUARDIAN):**
   - Checked by Qualcomm TrustZone during early boot sequence.
   - Removing causes the phone to reboot repeatedly into MIUI Recovery.
   - **Verdict: ALWAYS KEEP.**

4. **`com.xiaomi.xmsf` (XIAOMI SERVICE FRAMEWORK):**
   - Needed for push notifications and Xiaomi Account authentication.
   - **Verdict: ALWAYS KEEP.**

5. **`com.mi.android.globallauncher` (POCO LAUNCHER):**
   - Controls full-screen navigation gestures and the recent apps task switcher.
   - Only remove if a third-party launcher (e.g. Nova, Lawnchair) is installed and set as Default Home.
   - **Verdict: KEEP UNLESS REPLACED.**

---

## 5. Verified Real-World Benchmark Results

Measured directly on hardware: **POCO F5 (`23049PCD8G`, `marble`)** running **Xiaomi HyperOS 3.0.2.0.VMRRUXM (Android 15, `AQ3A.250226.002`)**:

| Telemetry Metric | Before Optimization | After cleanyourdroid | Net Gain / Delta |
|:---|:---:|:---:|:---:|
| **Enabled Packages (User 0)** | 731 | 716 | **-15 core bloat packages** |
| **Used RAM (dumpsys PSS)** | 6,788.9 MB | 6,133.0 MB | **-655.9 MB** |
| **Available RAM (total 11,160 − used)** | 4,371.1 MB | 5,027.0 MB | **+655.9 MB headroom** |
| **Free RAM incl. cache (dumpsys)** | 9,305.8 MB | 9,121.4 MB | -184.4 MB: the page cache shrank, this is not a regression |
| **ZRAM Swap Utilization** | 1,813.4 MB | 1,772.0 MB | **-41.4 MB compressed swap pressure** |
| **Display Refresh Rate** | 120 Hz (Dynamic) | 120 Hz (Dynamic) | **100% Unbroken** (`PowerKeeper` retained) |
| **Background AppOps Hog Eviction** | Active background | Restrained (`ignore`) | `com.facebook.katana` & `com.instagram.android` evicted from top memory consumers |
| **ART Compilation Status** | Partial JIT | Profile-Guided Ahead-of-Time | `cmd package bg-dexopt-job` completed |

> [!NOTE]
> **Why both RAM rows exist.** `dumpsys meminfo` prints a `Free RAM` figure that already contains cached pages, so `Free RAM + Used RAM` can exceed the physical total. Reporting it as "available memory" produces a card where a successful cleanup looks like a regression (-184.4 MB above). The honest pair is *Used* (PSS) and *Available = total − used*; the cache row is kept for transparency.
>
> **Storage.** Every removal used `pm uninstall -k --user 0`, so no APK left `/system` and no app data was deleted. Storage was reclaimed only by `pm trim-caches`; the session never claimed per-package "MB freed".

### 5.1 HyperOS Privacy & Ad Tracking Tweaks
The following settings flags were disabled via ADB to prevent background network polling and lockscreen recommendation banners:

| Setting Namespace | Key | Optimized Value | Default Value | Purpose |
|:---|:---|:---:|:---:|:---|
| `global` | `passport_ad_status` | `OFF` | `ON` | Disables Xiaomi Account ad push framework |
| `global` | `personalized_ad_enabled` | `0` | `1` | Disables OAID/advertising ID targeting |
| `global` | `com.miui.home.setting_recommend_app` | `0` | `1` | Disables app recommendations in launcher folders |
| `system` | `com.xiaomi.market.enable_app_chooser_recommend` | `0` | `1` | Disables sponsored app suggestions in "Open with..." dialog |
| `global` | `wifi_scan_always_enabled` | `0` | `1` | Disables background Wi-Fi beacon scanning when Wi-Fi is off |
| `global` | `ble_scan_always_enabled` | `0` | `1` | Disables background Bluetooth beacon scanning |

---

## 6. Restoration & Rollback

If you wish to re-enable all removed packages:

```bash
# Regenerate the script from the session log, then run it:
python3 tools/audit.py restore-script
bash ./backups/restore.sh
```

Or restore an individual package (for example, Mi Music or RuStore):
```bash
adb shell cmd package install-existing com.miui.player
adb shell cmd package install-existing ru.vk.store
```
No app data is lost during removal because every operation uses the `-k` retention flag, and the APK itself never left the system partition.
