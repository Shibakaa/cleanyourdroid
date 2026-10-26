#!/usr/bin/env python3
"""cleanyourdroid - deterministic debloat planner.

Cross-references the packages actually installed for user 0 against
``safety/known_bloatware.json`` and ``safety/bootloop_blacklist.json`` and
prints the same three groups the agent is supposed to present: safe removals,
preloaded OEM apps and items that need the user's decision.

Read-only: this tool never changes the device. It exists so the agent does not
have to eyeball a 700-line ``pm list packages`` dump, which is exactly where
wrong package names come from.

Examples
--------
    python3 tools/plan.py
    python3 tools/plan.py --format md
    python3 tools/plan.py --format json > backups/plan.json
    python3 tools/plan.py --packages-file backups/installed_packages_before.txt
    python3 tools/plan.py --validate
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adbkit import Adb, AdbError, repo_root  # noqa: E402

# Ensure UTF-8 output on Windows consoles with legacy encodings (cp1251, cp437...)
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

FILES = {
    "bloatware": Path("safety") / "known_bloatware.json",
    "blacklist": Path("safety") / "bootloop_blacklist.json",
}

GROUP_TITLES = OrderedDict(
    [
        ("ads_and_telemetry", "Group A - Ads & telemetry (safe removal)"),
        ("hidden_installers", "Group A - Hidden installers (safe removal)"),
        ("oem_bloat", "Group B - Preloaded OEM apps"),
        ("ru_region_preloads", "Group B - Regional statutory preloads"),
        ("google_pixel", "Group B - Preinstalled Google apps (safe removal)"),
        ("user_discretion", "Group C - Needs your decision"),
        ("tradeoff", "Group C - Needs your decision (behaviour changes)"),
    ]
)

DECISION_GROUPS = ("user_discretion", "tradeoff")


# --------------------------------------------------------------------- data


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit("Error: %s not found. Run this from the repository root." % path)
    except ValueError as exc:
        raise SystemExit("Error: %s is not valid JSON (%s)." % (path, exc))


def load_database():
    """Return (bloat entries indexed by package, blacklist set, categories)."""
    root = repo_root()
    bloat = load_json(root / FILES["bloatware"])
    blacklist = load_json(root / FILES["blacklist"])

    entries = {}
    duplicates = []
    for category, items in bloat.get("categories", {}).items():
        for item in items:
            package = item.get("package", "").strip()
            if not package:
                continue
            if package in entries:
                duplicates.append(package)
                continue
            entry = dict(item)
            entry["category"] = category
            entries[package] = entry

    protected = {}
    for category, items in blacklist.get("categories", {}).items():
        for item in items:
            package = item.get("package", "").strip()
            if package:
                protected[package] = dict(item, category=category)

    return entries, protected, duplicates


def read_packages_file(path):
    packages = []
    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit("Error: cannot read %s (%s)." % (path, exc.strerror or exc))
    with handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if " " in line:  # tolerate `package:com.x` plus trailing columns
                line = line.split()[0]
            if line.startswith("package:"):
                line = line[len("package:"):]
            line = line.strip()
            if line:
                packages.append(line)
    return sorted(set(packages))


def read_device(adb):
    info = {
        "brand": adb.getprop("ro.product.brand") or "Unknown",
        "model": adb.getprop("ro.product.model") or "Unknown",
        "device": adb.getprop("ro.product.device") or "Unknown",
        "android": adb.getprop("ro.build.version.release") or "Unknown",
        "build": adb.getprop("ro.build.display.id") or "Unknown",
        "serial": adb.serial,
    }
    return info


# ------------------------------------------------------------------- plan


def classify(entries, protected, installed, disabled):
    groups = OrderedDict((key, []) for key in GROUP_TITLES)
    unknown = []
    protected_present = []

    installed_set = set(installed)
    for package in sorted(installed_set):
        entry = entries.get(package)
        if entry is None:
            continue
        if package in protected:  # should never happen; guard anyway
            protected_present.append(protected[package])
            continue
        recommendation = entry.get("recommendation", "user_discretion")
        if recommendation == "safe_removal":
            bucket = entry["category"] if entry["category"] in groups else "ads_and_telemetry"
        elif recommendation == "optional_with_tradeoff":
            bucket = "tradeoff"
        else:
            bucket = "user_discretion"
        groups[bucket].append(entry)

    # Blacklisted packages that are actually on the device: informational,
    # proves the guard is live and is never a removal candidate.
    for package in sorted(installed_set):
        if package in protected and protected[package] not in protected_present:
            protected_present.append(protected[package])

    already_disabled = [entries[p] for p in sorted(set(disabled)) if p in entries]

    for package in sorted(set(disabled)):
        if package not in entries and package not in protected:
            unknown.append(package)

    return groups, protected_present, already_disabled, unknown


def plan_payload(entries, protected, installed, disabled, device, source):
    groups, protected_present, already_disabled, unknown = classify(
        entries, protected, installed, disabled
    )
    matched = sum(len(group) for group in groups.values())
    decisions = len(groups["user_discretion"]) + len(groups["tradeoff"])
    safe_removal = sum(
        len(items) for key, items in groups.items() if key not in DECISION_GROUPS
    )
    payload = {
        "source": source,
        "device": device,
        "counts": {
            "installed": len(installed),
            "candidates": matched,
            "safe_removal": safe_removal,
            "needs_decision": decisions,
            "already_disabled": len(already_disabled),
            "protected_present": len(protected_present),
            "unlisted_disabled": len(unknown),
        },
        "groups": OrderedDict((key, [trim(item) for item in groups[key]]) for key in groups),
        "protected_present": [item.get("package") for item in protected_present],
        "already_disabled": [item.get("package") for item in already_disabled],
        "unlisted_disabled": unknown,
    }
    return payload


def trim(entry):
    return {
        "package": entry.get("package"),
        "name": entry.get("name"),
        "oem": entry.get("oem"),
        "category": entry.get("category"),
        "recommendation": entry.get("recommendation"),
        "description": entry.get("description"),
        "impact": entry.get("impact"),
    }


# ------------------------------------------------------------------ render


def _clip(text, width):
    text = " ".join((text or "").split())
    return text if len(text) <= width else text[: width - 1].rstrip() + "\u2026"


def render_table(payload):
    lines = []
    device = payload.get("device") or {}
    header = "%s %s (%s) - Android %s" % (
        device.get("brand", "?"),
        device.get("model", "?"),
        device.get("device", "?"),
        device.get("android", "?"),
    )
    lines.append(header)
    if payload.get("source"):
        lines.append("packages: %s" % payload["source"])
    lines.append("")

    for key, title in GROUP_TITLES.items():
        items = payload["groups"].get(key, [])
        if not items:
            continue
        lines.append("%s  [%d]" % (title, len(items)))
        lines.append("-" * 78)
        for item in items:
            lines.append("  %-46s %s" % (item["package"], _clip(item.get("name"), 30)))
            lines.append("      %s" % _clip(item.get("description"), 70))
        lines.append("")

    counts = payload["counts"]
    lines.append(
        "installed %d | candidates %d | safe %d | decide %d | already off %d | protected %d"
        % (
            counts["installed"],
            counts["candidates"],
            counts["safe_removal"],
            counts["needs_decision"],
            counts["already_disabled"],
            counts["protected_present"],
        )
    )
    return "\n".join(lines)


def render_markdown(payload):
    counts = payload["counts"]
    lines = []
    device = payload.get("device") or {}
    lines.append(
        "### Plan for %s %s (%s), Android %s"
        % (
            device.get("brand", "?"),
            device.get("model", "?"),
            device.get("device", "?"),
            device.get("android", "?"),
        )
    )
    lines.append("")
    lines.append(
        "Installed: **%d** | candidates: **%d** | needs decision: **%d** | "
        "already disabled: **%d** | blacklisted & present: **%d**"
        % (
            counts["installed"],
            counts["candidates"],
            counts["needs_decision"],
            counts["already_disabled"],
            counts["protected_present"],
        )
    )
    lines.append("")

    for key, title in GROUP_TITLES.items():
        items = payload["groups"].get(key, [])
        if not items:
            continue
        lines.append("#### %s" % title)
        lines.append("")
        lines.append("| Package | What it is | Why | Risk |")
        lines.append("|:---|:---|:---|:---|")
        for item in items:
            risk = {
                "safe_removal": "Low",
                "user_discretion": "Low - your call",
                "optional_with_tradeoff": "Medium - trade-off",
            }.get(item.get("recommendation"), "Review")
            lines.append(
                "| `%s` | %s | %s | %s |"
                % (
                    item["package"],
                    item.get("name", ""),
                    _clip(item.get("impact") or item.get("description"), 90),
                    risk,
                )
            )
        lines.append("")

    protected = payload.get("protected_present") or []
    if protected:
        lines.append(
            "> %d blacklisted package(s) are present and will never be proposed "
            "(e.g. %s)." % (len(protected), ", ".join("`%s`" % p for p in protected[:3]))
        )
    return "\n".join(lines)


def render_json(payload):
    return json.dumps(payload, indent=2, ensure_ascii=False)


# -------------------------------------------------------------------- main


def build_parser():
    parser = argparse.ArgumentParser(
        description="Cross-reference installed packages with the cleanyourdroid safety databases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--serial", help="ADB serial of the target device")
    parser.add_argument("--adb", help="Path (or JSON argv array) to the adb binary")
    parser.add_argument(
        "--packages-file",
        help="Read packages from a file instead of the device (one per line, 'package:' optional)",
    )
    parser.add_argument(
        "--disabled-file",
        help="Read already-disabled packages from a file instead of the device",
    )
    parser.add_argument("--format", choices=("table", "md", "json"), default="table")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check the databases for duplicates and bloatware/blacklist overlaps",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    entries, protected, duplicates = load_database()

    problems = []
    if duplicates:
        problems.append("duplicate package(s) in known_bloatware.json: %s" % ", ".join(sorted(duplicates)))
    overlaps = sorted(set(entries) & set(protected))
    if overlaps:
        problems.append(
            "package(s) present in both databases: %s" % ", ".join(overlaps)
        )
    if args.validate:
        if problems:
            for problem in problems:
                print("[!] " + problem, file=sys.stderr)
            return 2
        print("[+] Databases OK: %d bloatware entries, %d protected packages, no overlap."
              % (len(entries), len(protected)))
        return 0

    for problem in problems:
        print("[!] " + problem, file=sys.stderr)

    if args.packages_file:
        installed = read_packages_file(args.packages_file)
        disabled = read_packages_file(args.disabled_file) if args.disabled_file else []
        device = {"brand": "Offline", "model": Path(args.packages_file).name, "device": "-", "android": "-"}
        source = "file:%s" % args.packages_file
    else:
        try:
            adb = Adb(binary=args.adb, serial=args.serial)
            device = read_device(adb)
            installed = adb.installed_packages()
            disabled = adb.disabled_packages()
            source = "device %s" % device["serial"]
        except AdbError as exc:
            print("[!] %s" % exc, file=sys.stderr)
            return 1

    if not installed:
        print("[!] No installed packages were returned. Is the device unlocked and authorized?", file=sys.stderr)
        return 1

    payload = plan_payload(entries, protected, installed, disabled, device, source)

    if args.format == "json":
        print(render_json(payload))
    elif args.format == "md":
        print(render_markdown(payload))
    else:
        print(render_table(payload))

    counts = payload["counts"]
    if counts["candidates"] == 0:
        print(
            "\n[+] Nothing in the database matches this device. The safe win here is tuning, "
            "not removal - see AGENTS.md Step 5.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.", file=sys.stderr)
        sys.exit(130)
