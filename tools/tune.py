#!/usr/bin/env python3
"""cleanyourdroid - rootless tuning that is not about packages.

Package removal gets the headlines, but most of what shell (UID 2000) can do
happens elsewhere: standby buckets, AppOps, Private DNS, animation scales, the
phantom-process killer. This tool exposes those as named tweaks, each with

* a plain-language description of what it changes,
* the exact command and the exact reverse command,
* a read-back check, and
* an entry in ``backups/actions.json``, so ``restore.sh`` undoes it too.

Nothing runs without ``--yes``: the default is a dry run that prints commands.

Examples
--------
    python3 tools/tune.py list
    python3 tools/tune.py status
    python3 tools/tune.py apply --id animations --id private_dns --yes
    python3 tools/tune.py apply --id standby --package com.facebook.katana --yes
    python3 tools/tune.py revert --id private_dns
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit  # noqa: E402  (shares the action log schema)
from adbkit import Adb, AdbError  # noqa: E402

DEFAULT_DNS = "dns.adguard-dns.com"

# Settings-based tweaks: (namespace, key, target value).
SETTINGS_TWEAKS = [
    {
        "id": "animations",
        "group": "ui",
        "title": "Faster animations (0.5x)",
        "why": "Window and menu transitions finish in half the time, which reads as a faster phone.",
        "risk": "cosmetic - Developer options can set it back to 1.0",
        "keys": [
            ("global", "window_animation_scale", "0.5"),
            ("global", "transition_animation_scale", "0.5"),
            ("global", "animator_duration_scale", "0.5"),
        ],
    },
    {
        "id": "scans",
        "group": "battery",
        "title": "Stop always-on Wi-Fi and Bluetooth scanning",
        "why": "Background beacon scans keep the radios busy even when Wi-Fi is off.",
        "risk": "low - location fixes that rely on Wi-Fi scans get slightly worse",
        "keys": [
            ("global", "wifi_scan_always_enabled", "0"),
            ("global", "ble_scan_always_enabled", "0"),
        ],
    },
    {
        "id": "private_dns",
        "group": "privacy",
        "title": "Private DNS ad blocking",
        "why": "The phone resolves names through AdGuard, so ad domains simply do not load in most apps. Nothing is installed.",
        "risk": "low - apps with their own DoH ignore it, and the DNS host must stay reachable",
        "keys": [
            ("global", "private_dns_mode", "hostname"),
            ("global", "private_dns_specifier", DEFAULT_DNS),
        ],
    },
    {
        "id": "phantom",
        "group": "battery",
        "title": "Stop the phantom process killer",
        "why": "Android silently kills background child processes; this is what kept terminating Termux sessions.",
        "risk": "medium - it is an out-of-memory safety valve, watch free RAM afterwards",
        "keys": [("global", "settings_enable_monitor_phantom_procs", "false")],
    },
]

# Package-scoped tweaks. `read` returns the current value, `apply`/`revert` take
# the package name; `revert` may use {previous}.
PACKAGE_TWEAKS = [
    {
        "id": "standby",
        "group": "battery",
        "title": "Restricted standby bucket",
        "why": "Android stops waking the app for jobs and alarms while the screen is off.",
        "risk": "medium - messages from this app may arrive late",
        "read": ["am", "get-standby-bucket"],
        "apply": "am set-standby-bucket {package} restricted",
        "revert": "am set-standby-bucket {package} {previous}",
    },
    {
        "id": "appops_bg",
        "group": "battery",
        "title": "No background execution (AppOps)",
        "why": "The app cannot start work on its own; it only runs when you open it.",
        "risk": "medium - this is the switch that silences push notifications",
        "read": ["cmd", "appops", "get", "{package}", "RUN_IN_BACKGROUND"],
        "apply": "cmd appops set {package} RUN_IN_BACKGROUND ignore",
        "revert": "cmd appops set {package} RUN_IN_BACKGROUND {previous}",
    },
    {
        "id": "overlay",
        "group": "privacy",
        "title": "No draw-over-other-apps",
        "why": "The app can no longer paint on top of the screen, which removes a whole class of tapjacking ads.",
        "risk": "low - some floating widgets stop working",
        "read": ["cmd", "appops", "get", "{package}", "SYSTEM_ALERT_WINDOW"],
        "apply": "cmd appops set {package} SYSTEM_ALERT_WINDOW deny",
        "revert": "cmd appops set {package} SYSTEM_ALERT_WINDOW {previous}",
    },
]

ALL_TWEAKS = SETTINGS_TWEAKS + PACKAGE_TWEAKS
BY_ID = {tweak["id"]: tweak for tweak in ALL_TWEAKS}

# am get-standby-bucket prints the numeric bucket on most builds.
BUCKET_NAMES = {10: "active", 20: "working_set", 30: "frequent", 40: "rare", 45: "restricted", 50: "never"}
BUCKET_DEFAULT = "active"


# ------------------------------------------------------------------ helpers


def read_setting(adb, namespace, key):
    value = adb.shell(["settings", "get", namespace, key]).strip()
    return "" if value in ("", "null") else value


def write_setting(adb, namespace, key, value):
    adb.shell(["settings", "put", namespace, key, str(value)])


def delete_setting(adb, namespace, key):
    adb.shell(["settings", "delete", namespace, key])


def read_appop(adb, package, op):
    output = adb.shell(["cmd", "appops", "get", package, op])
    for line in output.splitlines():
        if ":" not in line or line.strip().startswith("No operations"):
            continue
        name, _, mode = line.partition(":")
        if name.strip().upper() != op:
            continue
        # Newer builds append "; time=+1d2h" to the mode.
        return mode.split(";")[0].strip() or "default"
    return "default"


def read_bucket(adb, package):
    raw = adb.shell(["am", "get-standby-bucket", package]).strip()
    if raw.isdigit():
        return BUCKET_NAMES.get(int(raw), BUCKET_DEFAULT)
    return raw or BUCKET_DEFAULT


def run_shell_command(adb, command):
    """Run a stored ``adb shell ...`` command through the active client."""
    parts = command.split()
    if parts[:2] == ["adb", "shell"]:
        parts = parts[2:]
    elif parts[:1] == ["adb"]:
        parts = parts[1:]
    adb.shell(parts)


def device_stamp(adb):
    return {
        "brand": adb.getprop("ro.product.brand") or "Unknown",
        "model": adb.getprop("ro.product.model") or "Unknown",
        "device": adb.getprop("ro.product.device") or "Unknown",
        "android_version": adb.getprop("ro.build.version.release") or "Unknown",
        "build_id": adb.getprop("ro.build.display.id") or "Unknown",
        "serial": adb.serial,
    }


# ------------------------------------------------------------------- status


def tweak_status(adb, tweak, package=None):
    """Return ``[(label, current, target)]`` for display."""
    rows = []
    if "keys" in tweak:
        for namespace, key, target in tweak["keys"]:
            rows.append(("%s/%s" % (namespace, key), read_setting(adb, namespace, key), target))
        return rows

    if not package:
        return [("package", "(use --package)", "-")]
    if tweak["id"] == "standby":
        current = read_bucket(adb, package)
    else:
        current = read_appop(adb, package, tweak["read"][-1])
    target = tweak["apply"].split()[-1]
    return [("package", current, target)]


def cmd_list(args):
    groups = {}
    for tweak in ALL_TWEAKS:
        groups.setdefault(tweak["group"], []).append(tweak)
    for group in ("battery", "privacy", "ui"):
        if group not in groups:
            continue
        print("%s" % group)
        print("-" * 78)
        for tweak in groups[group]:
            scope = "package" if "keys" not in tweak else "settings"
            print("  %-12s %-58s [%s]" % (tweak["id"], tweak["title"][:58], scope))
            print("      %s" % tweak["why"])
            print("      risk: %s" % tweak["risk"])
        print("")
    return 0


def cmd_status(args):
    adb = Adb(binary=args.adb, serial=args.serial)
    print("Tweak status on %s %s\n" % (adb.getprop("ro.product.brand"), adb.getprop("ro.product.model")))
    for tweak in select_tweaks(args):
        try:
            rows = tweak_status(adb, tweak, args.package)
        except AdbError as exc:
            print("[!] %s" % exc, file=sys.stderr)
            return 1
        print("%-12s %s" % (tweak["id"], tweak["title"]))
        for label, current, target in rows:
            mark = "=" if current == target else " "
            print("  [%s] %-46s now: %-16s target: %s" % (mark, label, current or "(unset)", target))
        print("")
    return 0


# -------------------------------------------------------------------- apply


def apply_settings_tweak(adb, tweak, args, log_path, device):
    applied = 0
    for namespace, key, target in tweak["keys"]:
        if tweak["id"] == "private_dns" and key == "private_dns_specifier":
            target = args.dns
        previous = read_setting(adb, namespace, key)
        label = "%s/%s" % (namespace, key)
        command = "adb shell settings put %s %s %s" % (namespace, key, target)
        restore = (
            "adb shell settings put %s %s %s" % (namespace, key, previous)
            if previous
            else "adb shell settings delete %s %s" % (namespace, key)
        )

        if previous == target:
            print("  = %-38s already %s" % (label, target))
            continue
        if not args.yes:
            print("  would run: %s" % command)
            print("  to revert: %s" % restore)
            continue

        write_setting(adb, namespace, key, target)
        after = read_setting(adb, namespace, key)
        result = "ok" if after == target else "failed"
        audit.record_action(
            "settings", label, command, restore, result, tweak["title"], path=log_path, device=device
        )
        print("  %s %-38s %s -> %s" % ("+" if result == "ok" else "!", label, previous or "(unset)", after))
        applied += 1 if result == "ok" else 0
    return applied


def apply_package_tweak(adb, tweak, package, args, log_path, device):
    if not package:
        print("  ! %s needs --package" % tweak["id"], file=sys.stderr)
        return 0

    if tweak["id"] == "standby":
        previous = read_bucket(adb, package)
    else:
        previous = read_appop(adb, package, tweak["read"][-1])

    command = "adb shell " + tweak["apply"].format(package=package)
    restore = "adb shell " + tweak["revert"].format(package=package, previous=previous or BUCKET_DEFAULT)

    if not args.yes:
        print("  would run: %s" % command)
        print("  to revert: %s" % restore)
        return 0

    run_shell_command(adb, tweak["apply"].format(package=package))
    if tweak["id"] == "standby":
        after = read_bucket(adb, package)
    else:
        after = read_appop(adb, package, tweak["read"][-1])

    target = tweak["apply"].split()[-1]
    result = "ok" if after == target else "failed"
    audit.record_action(
        "appops", package, command, restore, result, tweak["title"], path=log_path, device=device
    )
    print("  %s %-32s %s -> %s" % ("+" if result == "ok" else "!", package, previous, after))
    return 1 if result == "ok" else 0


def cmd_apply(args):
    adb = Adb(binary=args.adb, serial=args.serial)
    log_path = Path(args.backups) / "actions.json"
    device = device_stamp(adb)

    if not args.yes:
        print("[i] Dry run: add --yes to execute. Nothing has been changed.\n")

    applied = 0
    for tweak in select_tweaks(args):
        print("%s - %s" % (tweak["id"], tweak["title"]))
        print("    %s" % tweak["why"])
        if "keys" in tweak:
            applied += apply_settings_tweak(adb, tweak, args, log_path, device)
        else:
            applied += apply_package_tweak(adb, tweak, args.package, args, log_path, device)
        print("")

    if args.yes:
        print("[+] %d change(s) applied and logged. Regenerate the reversal script with:" % applied)
        print("    python3 tools/audit.py restore-script")
    return 0


def cmd_revert(args):
    log_path = Path(args.backups) / "actions.json"
    data = audit.load_actions(log_path)
    if not data:
        print("Error: no action log, nothing to revert.", file=sys.stderr)
        return 1

    selected = select_tweaks(args)
    titles = {tweak["title"] for tweak in selected}
    settings_ids = {tweak["id"] for tweak in SETTINGS_TWEAKS}
    adb = Adb(binary=args.adb, serial=args.serial)

    reverted = 0
    for action in reversed(data["actions"]):
        if action.get("note") not in titles or not action.get("restore"):
            continue
        tweak_id = next(
            (tweak["id"] for tweak in selected if tweak["title"] == action.get("note")), None
        )
        if args.package and tweak_id not in settings_ids and action.get("target") != args.package:
            continue
        print("  reverting %s: %s" % (action.get("target"), action["restore"]))
        if args.yes:
            run_shell_command(adb, action["restore"])
        reverted += 1

    if not reverted:
        print("Nothing to revert for the selected tweaks.")
        return 0
    if not args.yes:
        print("\n[i] Dry run: add --yes to execute.")
    else:
        print("\n[+] %d revert command(s) executed." % reverted)
    return 0


# ---------------------------------------------------------------- selection


def select_tweaks(args):
    if getattr(args, "ids", None):
        return [BY_ID[tweak_id] for tweak_id in args.ids if tweak_id in BY_ID]
    if getattr(args, "group", None):
        return [tweak for tweak in ALL_TWEAKS if tweak["group"] == args.group]
    return list(ALL_TWEAKS)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Rootless Android tuning (standby buckets, AppOps, Private DNS, scales) with a dry run by default.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--adb", help="Path (or JSON argv array) to the adb binary")
    parser.add_argument("--serial", help="ADB serial of the target device")
    parser.add_argument("--backups", default="backups", help="Directory holding actions.json (default: backups)")

    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("list", help="Describe every known tweak (no device needed)")

    status = sub.add_parser("status", help="Show current values on the device")
    add_selection(status)

    apply = sub.add_parser("apply", help="Apply tweaks (dry run unless --yes)")
    add_selection(apply)
    apply.add_argument("--yes", action="store_true", help="Actually execute the commands")
    apply.add_argument("--dns", default=DEFAULT_DNS, help="Private DNS host (default: %s)" % DEFAULT_DNS)

    revert = sub.add_parser("revert", help="Undo tweaks recorded in actions.json")
    add_selection(revert)
    revert.add_argument("--yes", action="store_true", help="Actually execute the reverse commands")
    return parser


def add_selection(parser):
    parser.add_argument("--id", dest="ids", action="append", help="Tweak id (repeatable); default: all")
    parser.add_argument("--group", choices=("battery", "privacy", "ui"), help="Apply a whole group")
    parser.add_argument("--package", help="Package for package-scoped tweaks")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.subcommand != "list" and not (args.ids or args.group):
        if args.subcommand in ("status", "apply", "revert"):
            args.ids = [tweak["id"] for tweak in SETTINGS_TWEAKS]

    try:
        if args.subcommand == "list":
            return cmd_list(args)
        if args.subcommand == "status":
            return cmd_status(args)
        if args.subcommand == "apply":
            return cmd_apply(args)
        if args.subcommand == "revert":
            return cmd_revert(args)
    except AdbError as exc:
        print("[!] %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.", file=sys.stderr)
        return 130
    return 1


if __name__ == "__main__":
    sys.exit(main())
