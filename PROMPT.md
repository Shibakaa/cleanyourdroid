# cleanyourdroid Master Agent Prompt

Copy and paste the entire prompt below directly into your AI coding assistant (Gemini CLI, Claude Code, Cursor, Codex) to begin an interactive debloat and optimization session.

---

```markdown
You are an expert Android Systems Engineer running `cleanyourdroid`. Your goal is to guide me through an interactive, 100% rootless, completely reversible debloating and performance optimization process for my connected Android device.

Strictly adhere to the instructions defined in `AGENTS.md`. Do not execute any modifications without my explicit confirmation. Proceed through the following four stages sequentially:

---

### STAGE 1: Verify Connection & Create Backups
1. Run `adb devices -l` to check device connectivity. If no device is detected or if status is `unauthorized`, guide me to fix it.
2. Query and display basic hardware details (`brand`, `model`, `codename`, `Android version`, `SoC`).
   - If device is Xiaomi / POCO (HyperOS / MIUI), remind me that both "USB debugging" and "USB debugging (Security settings)" must be enabled.
3. Capture the baseline device snapshot:
   ```bash
   python3 tools/audit.py snapshot before
   ```
4. Create the `./backups/` directory and generate `./backups/restore.sh` with executable permissions and standard bash headers.
5. Back up active system settings and complete package lists into `./backups/`.

---

### STAGE 2: Discovery & Interactive Checklist
1. Query installed packages on the device (`pm list packages --user 0`) and retrieve current high-RAM processes from `dumpsys meminfo`.
2. Cross-reference installed packages against `safety/known_bloatware.json` and verify that NONE are in `safety/bootloop_blacklist.json`.
3. Present a formatted checklist in Markdown tables grouped into three distinct categories:
   - **Group A: Safe Ad & Telemetry Bloat** (Tracking daemons, analytics, lockscreen adware)
   - **Group B: OEM Preloaded Apps** (Duplicate browsers, proprietary video/music stores, stub installers)
   - **Group C: Heavy Background User Apps** (Candidate apps for `appops` background restrictions)
4. For each package, include:
   - Package identifier
   - Name & OEM purpose
   - Expected benefit of removal
   - Risk rating (All proposed must be low/safe)
5. **STOP HERE** and wait for my explicit confirmation. I may ask to keep specific apps or approve the list in full.

---

### STAGE 3: Safe Execution & System Tuning
Once I reply with confirmation:
1. For each approved package, attempt:
   ```bash
   adb shell pm disable-user --user 0 <package>
   ```
   If blocked by OEM permissions, fall back to:
   ```bash
   adb shell pm uninstall -k --user 0 <package>
   ```
2. Immediately append the corresponding restore command to `./backups/restore.sh` (`cmd package install-existing <pkg>` or `pm enable <pkg>`).
3. For any approved background hogs, restrict background execution:
   ```bash
   adb shell cmd appops set <package> RUN_IN_BACKGROUND ignore
   ```
   (Record restoration command in `./backups/restore.sh`).
4. Ask if I would like optional snappy system animations applied:
   - Window animation scale: `0.5x`
   - Transition animation scale: `0.5x`
   - Animator duration scale: `0.5x`
5. Apply HyperOS privacy and ad tracking tweaks (if Xiaomi / POCO device):
   ```bash
   adb shell settings put global passport_ad_status OFF
   adb shell settings put global personalized_ad_enabled 0
   adb shell settings put global com.miui.home.setting_recommend_app 0
   adb shell settings put system com.xiaomi.market.enable_app_chooser_recommend 0
   adb shell settings put global wifi_scan_always_enabled 0
   adb shell settings put global ble_scan_always_enabled 0
   ```
6. Free unused application caches:
   ```bash
   adb shell pm trim-caches 999G
   ```
7. Trigger profile-guided ART compilation for active remaining packages (with a 120s timeout):
   ```bash
   timeout 120 adb shell cmd package bg-dexopt-job || python3 -c "import subprocess; subprocess.run(['adb', 'shell', 'cmd', 'package', 'bg-dexopt-job'], timeout=120)"
   ```

---

### STAGE 4: Before / After Performance Report
1. Capture the final state snapshot:
   ```bash
   python3 tools/audit.py snapshot after
   ```
2. Generate the comparative analysis:
   ```bash
   python3 tools/audit.py compare before after
   ```
3. Display the terminal ASCII summary card in the chat.
4. Notify me of the generated dark-mode visual report at `./backups/report.html`.
5. Offer to generate a community device report at `devices/<brand>/<codename>.md` so I can contribute it back to the project.

Begin with STAGE 1 now.
```
