# cleanyourdroid — Gemini CLI entry point

**The authoritative protocol lives in [AGENTS.md](AGENTS.md).** Read that file and follow it before touching the device; this file exists because Gemini CLI loads `GEMINI.md` first.

Non-negotiable rules, repeated here so they survive a truncated context:

1. **Never guess a package name.** Get the plan from `python3 tools/plan.py` (it reads `safety/known_bloatware.json` and `safety/bootloop_blacklist.json`), not from memory.
2. **Never touch a blacklisted package**, even if the user asks. `safety/bootloop_blacklist.json` is the hard stop. Explain the bootloop risk instead.
3. **Confirm before every change.** Present the table, then wait for an explicit yes.
4. **Log before you move on.** Every executed command goes through
   `python3 tools/audit.py log-action --kind <kind> --target <pkg> --command "<cmd>" --restore "<reverse>" --result ok`.
   `backups/restore.sh` is generated from that log (`python3 tools/audit.py restore-script`); never hand-write it.
5. **Prefer disable over uninstall**, and `pm uninstall -k --user 0` only as the documented fallback. `-k` keeps app data and the APK stays in `/system` — this frees RAM, not storage. Say so.
6. **Prove it.** Report only what `audit.py compare` measured or `actions.json` logged.

Start with `AGENTS.md` section 5, step 1.
