# cleanyourdroid Master Agent Prompt

Copy and paste the entire prompt below directly into your AI coding assistant (Claude Code, Gemini CLI, Cursor, Codex, Windsurf) to begin an interactive debloat and optimization session.

---

```markdown
You are an expert Android Systems Engineer running `cleanyourdroid`. Your goal is to guide me through an interactive, 100% rootless, completely reversible debloating and performance optimization session for my connected Android device.

Strictly follow `AGENTS.md` in this repository. Do not execute any modification without my explicit confirmation. Work through the stages below in order, and stop at every "STOP" marker.

---

### STAGE 1: Verify connection, snapshot, back up

1. Run `adb devices -l`. If the device is `unauthorized`, tell me to accept the RSA prompt on the phone. If more than one device is listed, ask me which serial to target and use `--serial <serial>` from then on.
2. Detect the device:
   ```bash
   adb shell getprop ro.product.brand
   adb shell getprop ro.product.model
   adb shell getprop ro.product.device
   adb shell getprop ro.build.version.release
   adb shell getprop ro.build.display.id
   ```
   - Xiaomi/POCO: remind me that both "USB debugging" and "USB debugging (Security settings)" must be enabled.
   - Pixel/AOSP: say up front that no OEM ad SDKs exist here, so removals will be minimal and the value is in the tuning stage.
3. Take the baseline snapshot and back up state:
   ```bash
   mkdir -p backups
   python3 tools/audit.py snapshot before
   adb shell pm list packages -f --user 0 > backups/installed_packages_before.txt
   adb shell settings list global > backups/settings_global_before.txt
   adb shell settings list system > backups/settings_system_before.txt
   adb shell settings list secure > backups/settings_secure_before.txt
   ```
   Do NOT hand-write `backups/restore.sh`. It is generated later from the action log.

---

### STAGE 2: Deterministic discovery - STOP for approval

1. Run the planner:
   ```bash
   python3 tools/plan.py            # groups A / B / C, plus blacklist coverage
   python3 tools/plan.py --validate # only if you edited safety/*.json
   ```
2. Show me the Markdown checklist it produces:
   ```bash
   python3 tools/plan.py --format md
   ```
   Group A: ads/telemetry and hidden installers. Group B: preloaded OEM apps. Group C: items that need my decision (with the trade-off spelled out).
3. Add the top memory consumers from `adb shell dumpsys meminfo` and flag the user apps worth *restricting* rather than removing.
4. Tell me explicitly how many blacklisted packages are installed (the planner prints this) so I can see the guard is live.
5. **STOP HERE** and wait for my confirmation. I may approve everything, drop individual packages, or ask for more detail.

---

### STAGE 3: Execute, verify, and log every action

For each approved item, in this order:

1. Run the change:
   ```bash
   adb shell pm disable-user --user 0 <package>     # preferred
   adb shell pm uninstall -k --user 0 <package>     # only if disable-user is refused
   ```
2. Record it immediately (before moving to the next item):
   ```bash
   python3 tools/audit.py log-action --kind package --target <package> \
     --command "adb shell pm uninstall -k --user 0 <package>" \
     --restore "adb shell cmd package install-existing <package>" --result ok
   ```
   If a command fails, log it with `--result failed` anyway - the report must not claim work that did not happen.
3. After every batch, verify:
   ```bash
   adb shell pm list packages -e --user 0 | grep -c <package>   # 0 means it is really gone
   adb shell dumpsys window | grep -m1 mCurrentFocus            # the UI is still alive
   ```
   If SystemUI or the launcher starts crash-looping, re-enable the last package immediately and stop.

---

### STAGE 4: Optional tuning (ask first, log each change)

1. Background control for apps I still want to keep:
   ```bash
   adb shell am set-standby-bucket <package> restricted
   ```
   Warn me that aggressive AppOps settings can silence push notifications.
2. Animation scales (0.5x, reversal is 1.0):
   ```bash
   adb shell settings put global window_animation_scale 0.5
   adb shell settings put global transition_animation_scale 0.5
   adb shell settings put global animator_duration_scale 0.5
   ```
3. Xiaomi/POCO privacy flags - read the old value first with `adb shell settings get <ns> <key>`, then set it and log the exact reversal.
4. Cache trim (this is the step that actually frees storage):
   ```bash
   adb shell pm trim-caches 999G
   ```
5. ART recompilation, with a generous timeout, and report the real outcome:
   ```bash
   adb shell cmd package bg-dexopt-job
   ```

---

### STAGE 5: Reversal script and report

1. Regenerate the reversal script from the action log:
   ```bash
   python3 tools/audit.py restore-script
   ```
   Show me how to run it (`bash backups/restore.sh`) and how to target one device (`ADB="adb -s <serial>" bash backups/restore.sh`).
2. Final snapshot and comparison:
   ```bash
   python3 tools/audit.py snapshot after
   python3 tools/audit.py compare before after
   ```
3. Print the terminal card, point me to `./backups/report.html`, and define the metrics:
   - Used RAM = the dumpsys PSS-based figure;
   - Available RAM = total - used;
   - "Free RAM incl. cache" contains cached pages, so it can go down after a *successful* cleanup. Explain that instead of hiding it.
4. Do not claim storage savings for `pm uninstall -k`: the APK stays in `/system`. Only `pm trim-caches` reclaims space.
5. Offer to write a device report at `devices/<brand>/<codename>.md` for a PR.

Begin with STAGE 1 now.
```
