#!/usr/bin/env python3
"""
cleanyourdroid - Zero-dependency Android Device Audit & Telemetry Tool
Queries device properties, memory metrics, package statistics via ADB,
and generates terminal summary cards and self-contained HTML bento reports.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

# The tools sit side by side, so make `import adbkit` work from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from adbkit import Adb, AdbError  # noqa: E402  (sys.path is prepared above)

# Ensure UTF-8 output on Windows consoles with legacy encodings (e.g. cp1251, cp437)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


BACKUPS_DIR = Path("backups")

# Populated by main() from --adb / --serial. The client is created lazily so
# `compare` still works on a machine with neither a phone nor adb installed.
_ADB_OPTIONS = {}
_ADB = None


def adb_client():
    global _ADB
    if _ADB is None:
        _ADB = Adb(binary=_ADB_OPTIONS.get("binary"), serial=_ADB_OPTIONS.get("serial"))
    return _ADB


def run_adb_cmd(args, timeout=15):
    """Run an ADB command and return stdout, or an empty string on failure."""
    try:
        proc = adb_client().run(args, timeout=timeout)
    except AdbError as exc:
        raise RuntimeError(str(exc))
    if proc.returncode != 0:
        return ""
    return proc.stdout


def clean_int(val_str):
    """Convert string with commas to integer."""
    if not val_str:
        return 0
    cleaned = re.sub(r"[^\d]", "", val_str)
    return int(cleaned) if cleaned else 0


def get_device_info():
    """Retrieve hardware and OS metadata using getprop."""
    props = {
        "brand": run_adb_cmd(["shell", "getprop", "ro.product.brand"]).strip() or "Unknown",
        "model": run_adb_cmd(["shell", "getprop", "ro.product.model"]).strip() or "Unknown",
        "device": run_adb_cmd(["shell", "getprop", "ro.product.device"]).strip() or "Unknown",
        "android_version": run_adb_cmd(["shell", "getprop", "ro.build.version.release"]).strip() or "Unknown",
        "build_id": run_adb_cmd(["shell", "getprop", "ro.build.display.id"]).strip() or "Unknown",
        "security_patch": run_adb_cmd(["shell", "getprop", "ro.build.version.security_patch"]).strip() or "Unknown",
        "soc": run_adb_cmd(["shell", "getprop", "ro.soc.model"]).strip()
        or run_adb_cmd(["shell", "getprop", "ro.board.platform"]).strip()
        or run_adb_cmd(["shell", "getprop", "ro.hardware"]).strip()
        or "Unknown",
        "serial": run_adb_cmd(["get-serialno"]).strip() or "Unknown",
    }
    return props


def parse_meminfo():
    """Parse RAM metrics and top processes from dumpsys, with /proc/meminfo fallback.

    Metric definitions matter here, because the published numbers are only
    meaningful when they add up:

    * ``used_ram_mb``       - dumpsys "Used RAM" (PSS based)
    * ``free_ram_mb``       - dumpsys "Free RAM", which *includes* cached pages
    * ``available_ram_mb``  - total - used, i.e. headroom without swapping
    * ``mem_available_mb``  - kernel MemAvailable, the honest "free" figure

    dumpsys "Free RAM" plus "Used RAM" can exceed total RAM on devices with a
    large page cache, so neither is reported as "available memory".
    """
    raw_mem = run_adb_cmd(["shell", "dumpsys", "meminfo"])
    metrics = {
        "total_ram_mb": 0,
        "free_ram_mb": 0,
        "used_ram_mb": 0,
        "available_ram_mb": 0,
        "mem_available_mb": 0,
        "cached_ram_mb": 0,
        "zram_used_mb": 0,
        "top_processes": [],
        "source": "dumpsys",
    }

    if raw_mem:
        # Extract RAM totals (values usually in kB)
        total_m = re.search(r"Total RAM:\s*([0-9,]+)\s*(?:kB|K)?", raw_mem, re.IGNORECASE)
        free_m = re.search(r"Free RAM:\s*([0-9,]+)\s*(?:kB|K)?", raw_mem, re.IGNORECASE)
        used_m = re.search(r"Used RAM:\s*([0-9,]+)\s*(?:kB|K)?", raw_mem, re.IGNORECASE)
        zram_m = re.search(r"ZRAM:\s*([0-9,]+)\s*(?:kB|K)?", raw_mem, re.IGNORECASE)

        if total_m:
            metrics["total_ram_mb"] = round(clean_int(total_m.group(1)) / 1024, 1)
        if free_m:
            metrics["free_ram_mb"] = round(clean_int(free_m.group(1)) / 1024, 1)
        if used_m:
            metrics["used_ram_mb"] = round(clean_int(used_m.group(1)) / 1024, 1)
        if zram_m:
            metrics["zram_used_mb"] = round(clean_int(zram_m.group(1)) / 1024, 1)

        # Look for cached breakdown inside Free RAM
        cached_m = re.search(r"\(\s*([0-9,]+)\s*(?:kB|K)?\s+cached pss", raw_mem, re.IGNORECASE)
        if cached_m:
            metrics["cached_ram_mb"] = round(clean_int(cached_m.group(1)) / 1024, 1)

        # Parse top processes under "Total PSS by process:"
        in_process_section = False
        top_procs = []
        for line in raw_mem.splitlines():
            line_str = line.strip()
            if "Total PSS by process:" in line:
                in_process_section = True
                continue
            if in_process_section:
                if not line_str or line_str.startswith("Total PSS") or line_str.startswith("Total RAM"):
                    break
                # Example: "142,384K: com.android.systemui (pid 1823)"
                proc_m = re.match(r"^([0-9,]+)\s*(?:kB|K)?:\s*([^\s(]+)(?:\s*\(pid\s*(\d+)\))?", line_str)
                if proc_m:
                    pss_kb = clean_int(proc_m.group(1))
                    proc_name = proc_m.group(2)
                    top_procs.append({
                        "process": proc_name,
                        "pss_mb": round(pss_kb / 1024, 1),
                    })
                    if len(top_procs) >= 10:
                        break
        metrics["top_processes"] = top_procs

    # The kernel view: always cheap, and the only trustworthy "free" number.
    proc_mem = run_adb_cmd(["shell", "cat", "/proc/meminfo"])
    if proc_mem:
        mem_tot = re.search(r"MemTotal:\s*(\d+)\s*kB", proc_mem)
        mem_free = re.search(r"MemFree:\s*(\d+)\s*kB", proc_mem)
        mem_avail = re.search(r"MemAvailable:\s*(\d+)\s*kB", proc_mem)
        mem_cached = re.search(r"^Cached:\s*(\d+)\s*kB", proc_mem, re.MULTILINE)

        if mem_tot:
            proc_total = round(int(mem_tot.group(1)) / 1024, 1)
            if metrics["total_ram_mb"] == 0:
                metrics["total_ram_mb"] = proc_total
                metrics["source"] = "proc"
        if mem_avail:
            metrics["mem_available_mb"] = round(int(mem_avail.group(1)) / 1024, 1)

        # Fallback when dumpsys was unavailable or returned nothing useful.
        if metrics["total_ram_mb"] > 0 and metrics["used_ram_mb"] == 0:
            if mem_avail:
                available = round(int(mem_avail.group(1)) / 1024, 1)
            elif mem_free:
                available = round(int(mem_free.group(1)) / 1024, 1)
            elif metrics["mem_available_mb"]:
                available = metrics["mem_available_mb"]
            else:
                available = metrics["free_ram_mb"]
            if available:
                metrics["free_ram_mb"] = available
                metrics["used_ram_mb"] = round(metrics["total_ram_mb"] - available, 1)
                metrics["source"] = "proc"
        if mem_cached and metrics["cached_ram_mb"] == 0:
            metrics["cached_ram_mb"] = round(int(mem_cached.group(1)) / 1024, 1)

    if metrics["total_ram_mb"] > 0 and metrics["used_ram_mb"] > 0:
        metrics["available_ram_mb"] = round(metrics["total_ram_mb"] - metrics["used_ram_mb"], 1)
    elif metrics["mem_available_mb"]:
        metrics["available_ram_mb"] = metrics["mem_available_mb"]

    return metrics


def get_enabled_packages():
    """Retrieve list of enabled packages for user 0."""
    raw = run_adb_cmd(["shell", "pm", "list", "packages", "-e", "--user", "0"])
    packages = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            pkg = line.replace("package:", "").strip()
            if pkg:
                packages.append(pkg)
    packages.sort()
    return packages


def cmd_snapshot(label):
    """Execute snapshot command and save to backups/<label>.json."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = BACKUPS_DIR / f"{label}.json"

    print(f"[*] Taking system snapshot '{label}' via ADB...")

    device_info = get_device_info()
    meminfo = parse_meminfo()
    packages = get_enabled_packages()

    snapshot_data = {
        "label": label,
        "timestamp": datetime.datetime.now().isoformat(),
        "device": device_info,
        "memory": meminfo,
        "packages": {
            "total_enabled_count": len(packages),
            "list": packages,
        },
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)

    print(f"[+] Snapshot successfully saved to: {out_file}")
    print(f"    - Device: {device_info['brand']} {device_info['model']} ({device_info['device']})")
    print(f"    - Android Version: {device_info['android_version']} (Build: {device_info['build_id']})")
    print(f"    - Total RAM: {meminfo['total_ram_mb']} MB | Available: {meminfo['available_ram_mb']} MB"
          f" (free incl. cache: {meminfo['free_ram_mb']} MB)")
    print(f"    - Enabled Packages: {len(packages)}")


def generate_html_report(before_data, after_data, diff, output_path, actions=None):
    """Generate a sleek, dark-mode bento grid HTML report.

    Everything the report asserts comes from the snapshots or from the action
    log written by ``log-action``; nothing is hardcoded as "already done".
    """
    device = after_data.get("device", before_data.get("device", {}))
    brand_model = f"{device.get('brand', 'Android').capitalize()} {device.get('model', 'Device')}"
    codename = device.get("device", "generic")
    soc = device.get("soc", "ARM64")
    android_ver = device.get("android_version", "14")
    build_id = device.get("build_id", "N/A")

    pkgs_before = before_data["packages"]["total_enabled_count"]
    pkgs_after = after_data["packages"]["total_enabled_count"]
    pkgs_diff = diff["packages_removed"]

    def memory_value(data, key):
        return data.get("memory", {}).get(key, 0) or 0

    total_ram = memory_value(after_data, "total_ram_mb") or memory_value(before_data, "total_ram_mb")
    used_before = memory_value(before_data, "used_ram_mb")
    used_after = memory_value(after_data, "used_ram_mb")
    avail_before = memory_value(before_data, "available_ram_mb") or round(total_ram - used_before, 1)
    avail_after = memory_value(after_data, "available_ram_mb") or round(total_ram - used_after, 1)
    free_before = memory_value(before_data, "free_ram_mb")
    free_after = memory_value(after_data, "free_ram_mb")
    ram_freed = diff["ram_freed_mb"]

    avail_delta = round(avail_after - avail_before, 1)
    avail_delta_display = f"+{avail_delta}" if avail_delta >= 0 else f"{avail_delta}"

    removed_list = diff.get("removed_packages_list", [])

    # Action log: only kinds that were actually recorded get a check mark.
    action_counts = {}
    failed_count = 0
    for action in (actions or {}).get("actions", []):
        result = (action.get("result") or "").lower()
        if result in ("ok", "already", "noop"):
            kind = (action.get("kind") or "other").lower()
            action_counts[kind] = action_counts.get(kind, 0) + 1
        elif result == "failed":
            failed_count += 1

    action_labels = [
        ("package", "Packages disabled / removed"),
        ("appops", "AppOps restrictions"),
        ("settings", "Settings changed"),
        ("dexopt", "ART recompilation"),
        ("cache", "Cache trimmed"),
        ("other", "Other actions"),
    ]
    tiles = []
    for kind, label in action_labels:
        if action_counts.get(kind):
            tiles.append(
                f"<div class='spec-item'><div class='spec-label'>{label}</div>"
                f"<div class='spec-val text-emerald'>&#10003; {action_counts[kind]} logged</div></div>"
            )
    if tiles:
        action_tiles = "".join(tiles)
        action_note = (
            f"<p class='kpi-subtext'>Read from <code>backups/actions.json</code>: "
            f"{sum(action_counts.values())} recorded action(s)"
            + (f", {failed_count} failed" if failed_count else "")
            + ". Reversal: <code>bash backups/restore.sh</code>.</p>"
        )
    else:
        action_tiles = (
            "<div class='spec-item' style='grid-column: span 2;'>"
            "<div class='spec-label'>Action log</div>"
            "<div class='spec-val' style='color:var(--text-muted);'>not recorded</div></div>"
        )
        action_note = (
            "<p class='kpi-subtext'>No <code>backups/actions.json</code>, so this card shows only the measured "
            "snapshot diff. Record every change with <code>tools/audit.py log-action</code> so the report and "
            "the reversal script stay in sync.</p>"
        )

    has_restore = any((action.get("restore") or "").strip() for action in (actions or {}).get("actions", []))
    reversibility_badge = (
        '<span class="badge badge-sky">&#10003; Reversible (restore.sh)</span>'
        if has_restore
        else '<span class="badge">&#9888; No reversal script recorded</span>'
    )
    if has_restore and failed_count == 0:
        package_badge = "User 0 scope"
    else:
        package_badge = "User 0 scope &bull; check log"

    # Process lists
    top_before = before_data["memory"].get("top_processes", [])[:8]
    top_after = after_data["memory"].get("top_processes", [])[:8]

    def render_proc_rows(procs):
        if not procs:
            return "<tr><td colspan='2' style='text-align:center; color:#64748b;'>No process telemetry available</td></tr>"
        rows = []
        for p in procs:
            rows.append(
                f"<tr><td class='font-mono'>{p.get('process')}</td>"
                f"<td class='text-right font-mono text-emerald'>{p.get('pss_mb')} MB</td></tr>"
            )
        return "\n".join(rows)

    removed_chips = "".join([f"<span class='chip'>{pkg}</span>" for pkg in removed_list[:40]])
    if len(removed_list) > 40:
        removed_chips += f"<span class='chip chip-more'>+{len(removed_list) - 40} more</span>"

    ram_freed_display = f"+{ram_freed}" if ram_freed >= 0 else f"{ram_freed}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>cleanyourdroid Optimization Report &bull; {brand_model}</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: rgba(20, 26, 42, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover: rgba(255, 255, 255, 0.12);
      --emerald: #10b981;
      --emerald-glow: rgba(16, 185, 129, 0.15);
      --sky: #38bdf8;
      --indigo: #818cf8;
      --rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      background-image: 
        radial-gradient(circle at 15% 10%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 80%, rgba(16, 185, 129, 0.08) 0%, transparent 40%);
      color: var(--text-main);
      font-family: var(--font-sans);
      min-height: 100vh;
      padding: 2.5rem 1.5rem;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }}
    .container {{
      max-width: 1100px;
      width: 100%;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .logo-icon {{
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #10b981, #06b6d4);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.25rem;
      color: #041017;
      box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }}
    .brand h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .brand span.tagline {{
      color: var(--text-muted);
      font-size: 0.875rem;
      display: block;
    }}
    .badge-bar {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
    }}
    .badge-success {{
      background: rgba(16, 185, 129, 0.12);
      border-color: rgba(16, 185, 129, 0.3);
      color: #34d399;
    }}
    .badge-sky {{
      background: rgba(56, 189, 248, 0.12);
      border-color: rgba(56, 189, 248, 0.3);
      color: var(--sky);
    }}
    .bento-grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 1.25rem;
    }}
    .card {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.5rem;
      transition: border-color 0.2s ease, transform 0.2s ease;
      position: relative;
      overflow: hidden;
    }}
    .card:hover {{
      border-color: var(--card-hover);
    }}
    .col-4 {{ grid-column: span 4; }}
    .col-6 {{ grid-column: span 6; }}
    .col-8 {{ grid-column: span 8; }}
    .col-12 {{ grid-column: span 12; }}
    @media (max-width: 860px) {{
      .col-4, .col-6, .col-8 {{ grid-column: span 12; }}
    }}
    .card-title {{
      font-size: 0.8125rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 0.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .kpi-value {{
      font-size: 2.75rem;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.04em;
      margin-bottom: 0.5rem;
    }}
    .kpi-delta {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.875rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
    }}
    .kpi-delta.positive {{
      background: rgba(16, 185, 129, 0.15);
      color: var(--emerald);
    }}
    .kpi-subtext {{
      color: var(--text-muted);
      font-size: 0.8125rem;
      margin-top: 0.5rem;
    }}
    .spec-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      margin-top: 0.5rem;
    }}
    .spec-item {{
      background: rgba(255, 255, 255, 0.03);
      padding: 0.75rem 1rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.04);
    }}
    .spec-label {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-bottom: 0.25rem;
    }}
    .spec-val {{
      font-size: 0.95rem;
      font-weight: 600;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8125rem;
      margin-top: 0.5rem;
    }}
    th {{
      text-align: left;
      color: var(--text-muted);
      font-weight: 500;
      padding: 0.4rem 0.5rem;
      border-bottom: 1px solid var(--card-border);
    }}
    td {{
      padding: 0.5rem 0.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }}
    .font-mono {{ font-family: var(--font-mono); }}
    .text-right {{ text-align: right; }}
    .text-emerald {{ color: var(--emerald); }}
    .chips-wrapper {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      max-height: 180px;
      overflow-y: auto;
      margin-top: 0.5rem;
      padding-right: 0.5rem;
    }}
    .chip {{
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.2);
      color: #fda4af;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      white-space: nowrap;
    }}
    .chip-more {{
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--card-border);
      color: var(--text-muted);
    }}
    footer {{
      margin-top: 2.5rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.8125rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--card-border);
      padding-top: 1.5rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    footer a {{
      color: var(--sky);
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="logo-icon">&#10003;</div>
        <div>
          <h1>cleanyourdroid</h1>
          <span class="tagline">Rootless Agentic Android Debloater & System Optimizer</span>
        </div>
      </div>
      <div class="badge-bar">
        <span class="badge badge-success">&#9679; 100% Rootless</span>
        {reversibility_badge}
        <span class="badge">{datetime.date.today().isoformat()}</span>
      </div>
    </header>

    <div class="bento-grid">
      <!-- KPI 1: Debloated Packages -->
      <div class="card col-4">
        <div class="card-title">Packages Eliminated</div>
        <div class="kpi-value text-emerald">-{pkgs_diff}</div>
        <div>
          <span class="kpi-delta positive">&darr; {pkgs_before} &rarr; {pkgs_after} active</span>
        </div>
        <p class="kpi-subtext">User-0 package state only &mdash; the APK stays in the system partition.</p>
      </div>

      <!-- KPI 2: Active RAM Freed -->
      <div class="card col-4">
        <div class="card-title">Active RAM Freed</div>
        <div class="kpi-value text-emerald">{ram_freed_display} <span style="font-size:1.25rem; font-weight:600;">MB</span></div>
        <div>
          <span class="kpi-delta positive">&darr; {used_before} MB &rarr; {used_after} MB used</span>
        </div>
        <p class="kpi-subtext">dumpsys "Used RAM" (PSS based) before and after the session.</p>
      </div>

      <!-- KPI 3: Available RAM -->
      <div class="card col-4">
        <div class="card-title">Available RAM</div>
        <div class="kpi-value" style="color:var(--sky);">{avail_after} <span style="font-size:1.25rem; font-weight:600;">MB</span></div>
        <div>
          <span class="badge">{avail_delta_display} MB vs baseline</span>
        </div>
        <p class="kpi-subtext">Total {total_ram} MB &minus; used. Free RAM incl. cache was {free_before} &rarr; {free_after} MB.</p>
      </div>

      <!-- Device Spec Overview -->
      <div class="card col-6">
        <div class="card-title">Device Specifications</div>
        <div class="spec-grid">
          <div class="spec-item">
            <div class="spec-label">Device Model</div>
            <div class="spec-val">{brand_model} ({codename})</div>
          </div>
          <div class="spec-item">
            <div class="spec-label">Processor / SoC</div>
            <div class="spec-val">{soc}</div>
          </div>
          <div class="spec-item">
            <div class="spec-label">Android OS</div>
            <div class="spec-val">Android {android_ver}</div>
          </div>
          <div class="spec-item">
            <div class="spec-label">OS Build</div>
            <div class="spec-val font-mono" style="font-size:0.8rem;">{build_id}</div>
          </div>
        </div>
      </div>

      <!-- System Tuning Applied (from the action log, never assumed) -->
      <div class="card col-6">
        <div class="card-title">System Optimizations Logged</div>
        <div class="spec-grid">
          {action_tiles}
        </div>
        {action_note}
      </div>

      <!-- Removed Packages List -->
      <div class="card col-12">
        <div class="card-title">
          <span>Decommissioned Packages & Telemetry ({len(removed_list)} Total)</span>
          <span class="badge">{package_badge}</span>
        </div>
        <div class="chips-wrapper">
          {removed_chips or '<span style="color:var(--text-muted);">No packages were removed.</span>'}
        </div>
      </div>

      <!-- Top RAM Consumers (Before vs After) -->
      <div class="card col-6">
        <div class="card-title">Top Memory Consuming Processes (Before)</div>
        <table>
          <thead>
            <tr><th>Process</th><th class="text-right">PSS (MB)</th></tr>
          </thead>
          <tbody>
            {render_proc_rows(top_before)}
          </tbody>
        </table>
      </div>

      <div class="card col-6">
        <div class="card-title">Top Memory Consuming Processes (After)</div>
        <table>
          <thead>
            <tr><th>Process</th><th class="text-right">PSS (MB)</th></tr>
          </thead>
          <tbody>
            {render_proc_rows(top_after)}
          </tbody>
        </table>
      </div>
    </div>

    <footer>
      <div>Generated by <strong>cleanyourdroid</strong> &bull; Open-source Android Optimizer</div>
      <div>Zero-Blindness Policy &bull; <a href="https://github.com/Gathin23/cleanyourtv" target="_blank" rel="noreferrer">Inspired by cleanyourtv</a></div>
    </footer>
  </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def load_actions(path=None):
    """Return the recorded action log, or ``None`` when nothing was logged."""
    path = Path(path) if path else BACKUPS_DIR / "actions.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except ValueError:
        print(f"[!] {path} is not valid JSON; ignoring it.", file=sys.stderr)
        return None
    if isinstance(data, list):
        data = {"version": 1, "actions": data}
    if not isinstance(data, dict) or not isinstance(data.get("actions"), list):
        print(f"[!] {path} has no 'actions' list; ignoring it.", file=sys.stderr)
        return None
    return data


def save_actions(data, path=None):
    path = Path(path) if path else BACKUPS_DIR / "actions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def record_action(kind, target, command="", restore="", result="ok", note="", path=None, device=None):
    """Append one action to the log and return the log data.

    Shared by audit.py and tune.py so both tools write the same schema into
    ``backups/actions.json`` and, therefore, into ``restore.sh``.
    """
    data = load_actions(path) or {
        "version": 1,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "device": {},
        "actions": [],
    }
    if device and not data.get("device"):
        data["device"] = device
    data["actions"].append(
        {
            "kind": kind,
            "target": target,
            "command": (command or "").strip(),
            "restore": (restore or "").strip(),
            "result": result,
            "note": (note or "").strip(),
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_actions(data, path)
    return data


def cmd_log_action(args):
    """Append one change to backups/actions.json (the single source of truth)."""
    device = {}
    if not args.no_device_probe:
        info = get_device_info()
        device = {
            key: info.get(key)
            for key in ("brand", "model", "device", "android_version", "build_id", "serial")
        }
    action = {
        "kind": args.kind,
        "target": args.target,
        "command": (args.command or "").strip(),
        "restore": (args.restore or "").strip(),
        "result": args.result,
        "note": (args.note or "").strip(),
    }
    data = record_action(args.kind, args.target, action["command"], action["restore"],
                         args.result, action["note"], path=args.actions, device=device)
    total = len(data["actions"])
    print(f"[+] Logged {args.kind} -> {args.target} ({args.result}). Actions recorded: {total}.")
    if not action["restore"] and args.result == "ok":
        print("[!] No --restore command given: this action cannot be undone by restore.sh.", file=sys.stderr)


def cmd_restore_script(args):
    """Render backups/restore.sh from the action log, newest action first."""
    data = load_actions(args.actions)
    if not data or not data.get("actions"):
        print("Error: no action log found, so there is nothing to reverse.", file=sys.stderr)
        return 1

    reversible = [
        action
        for action in reversed(data["actions"])
        if (action.get("restore") or "").strip() and action.get("result") in ("ok", "already", "noop")
    ]
    if not reversible:
        print("Error: none of the logged actions has a restore command.", file=sys.stderr)
        return 1

    device = data.get("device") or {}
    lines = [
        "#!/usr/bin/env bash",
        "# ==============================================================================",
        "# cleanyourdroid reversal script",
        "# Generated from backups/actions.json - do not edit by hand, re-run:",
        "#   python3 tools/audit.py restore-script",
        f"# Device: {device.get('brand', '?')} {device.get('model', '?')} "
        f"({device.get('device', '?')}) - Android {device.get('android_version', '?')}",
        f"# Actions: {len(reversible)} reversible of {len(data['actions'])} recorded",
        "# ==============================================================================",
        "set -euo pipefail",
        "",
        '# Override with: ADB="adb -s <serial>" bash backups/restore.sh',
        'ADB=${ADB:-adb}',
        "",
    ]
    for action in reversible:
        restore = " ".join(action["restore"].split())
        if restore.startswith("adb "):
            restore = "${ADB}" + restore[len("adb"):]
        note = action.get("target") or action.get("kind") or "action"
        lines.append(f"# {action.get('kind', 'action')}: {note}")
        lines.append(f'{restore} || echo "[!] failed: {restore}" >&2')
        lines.append("")
    lines.append('echo "[+] Done. Reboot the phone to be sure."')

    target = Path(args.output) if args.output else BACKUPS_DIR / "restore.sh"
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    try:
        if args.output is None:
            os.chmod(target, 0o755)
    except OSError:
        pass
    print(f"[+] Reversal script written to {target} ({len(reversible)} commands).")
    return 0


def cmd_compare(before_label, after_label, actions_path=None):
    """Compare two snapshots, render terminal ASCII card, and save report.html."""
    before_file = BACKUPS_DIR / f"{before_label}.json"
    after_file = BACKUPS_DIR / f"{after_label}.json"

    if not before_file.exists():
        print(f"Error: Before snapshot '{before_file}' does not exist.", file=sys.stderr)
        sys.exit(1)
    if not after_file.exists():
        print(f"Error: After snapshot '{after_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(before_file, "r", encoding="utf-8") as f:
            before_data = json.load(f)
        with open(after_file, "r", encoding="utf-8") as f:
            after_data = json.load(f)
    except ValueError as exc:
        print(f"Error: a snapshot is corrupt ({exc}). Re-run `snapshot`.", file=sys.stderr)
        sys.exit(1)

    actions = load_actions(actions_path)

    # Compute deltas
    b_pkgs = set(before_data.get("packages", {}).get("list", []))
    a_pkgs = set(after_data.get("packages", {}).get("list", []))
    removed_packages = sorted(list(b_pkgs - a_pkgs))

    b_pkg_count = before_data.get("packages", {}).get("total_enabled_count", len(b_pkgs))
    a_pkg_count = after_data.get("packages", {}).get("total_enabled_count", len(a_pkgs))
    pkgs_removed_count = b_pkg_count - a_pkg_count

    b_free_ram = before_data.get("memory", {}).get("free_ram_mb", 0) or 0
    a_free_ram = after_data.get("memory", {}).get("free_ram_mb", 0) or 0
    free_delta = round(a_free_ram - b_free_ram, 1)

    b_used_ram = before_data.get("memory", {}).get("used_ram_mb", 0) or 0
    a_used_ram = after_data.get("memory", {}).get("used_ram_mb", 0) or 0
    used_delta = round(b_used_ram - a_used_ram, 1)

    # Available RAM is total - used; older snapshots predate the field.
    total_ram = after_data.get("memory", {}).get("total_ram_mb", 0) or before_data.get("memory", {}).get("total_ram_mb", 0) or 0
    b_avail_ram = before_data.get("memory", {}).get("available_ram_mb") or (round(total_ram - b_used_ram, 1) if total_ram else b_free_ram)
    a_avail_ram = after_data.get("memory", {}).get("available_ram_mb") or (round(total_ram - a_used_ram, 1) if total_ram else a_free_ram)
    avail_delta = round(a_avail_ram - b_avail_ram, 1)

    ram_freed = used_delta if used_delta > 0 else free_delta

    device = after_data.get("device", before_data.get("device", {}))
    device_title = f"{device.get('brand', 'Android').capitalize()} {device.get('model', 'Device')} ({device.get('device', 'generic')})"
    build_str = f"Android {device.get('android_version', 'N/A')} ({device.get('build_id', 'N/A')})"
    soc_str = str(device.get('soc', 'N/A'))

    diff = {
        "packages_removed": pkgs_removed_count,
        "ram_freed_mb": ram_freed,
        "used_ram_reduction_mb": used_delta,
        "available_before_mb": b_avail_ram,
        "available_after_mb": a_avail_ram,
        "available_delta_mb": avail_delta,
        "free_delta_mb": free_delta,
        "removed_packages_list": removed_packages,
    }

    def signed(value, positive_prefix="+", negative_prefix=""):
        if value > 0:
            return f"{positive_prefix}{value}"
        if value < 0:
            return f"{value}"
        return "0.0"

    used_sign = f"-{used_delta}" if used_delta > 0 else signed(used_delta, "+", "")
    avail_sign = signed(avail_delta)
    free_sign = signed(free_delta)
    ram_freed_hdr = signed(ram_freed)

    def row(label, before, after, delta):
        return f"│ {label:<26}│ {before:<12} │ {after:<12} │ {delta:<12} │"

    def note(text):
        return f"│ {text[:71]:<71}│"

    card = "\n".join(
        [
            "┌────────────────────────────────────────────────────────────────────────┐",
            "│                      CLEANYOURDROID OPTIMIZATION REPORT                │",
            "├────────────────────────────────────────────────────────────────────────┤",
            f"│ Device:           {device_title[:53]:<53}│",
            f"│ OS & Build:       {build_str[:53]:<53}│",
            f"│ Chipset / SoC:    {soc_str[:53]:<53}│",
            "├────────────────────────────────────────────────────────────────────────┤",
            "│ METRIC                    │ BEFORE       │ AFTER        │ DELTA        │",
            "├───────────────────────────┼──────────────┼──────────────┼──────────────┤",
            row("Enabled Packages", b_pkg_count, a_pkg_count, f"-{pkgs_removed_count}"),
            row("Used RAM (PSS)", f"{b_used_ram} MB", f"{a_used_ram} MB", f"{used_sign} MB"),
            row("Available RAM", f"{b_avail_ram} MB", f"{a_avail_ram} MB", f"{avail_sign} MB"),
            row("Free RAM (incl. cache)", f"{b_free_ram} MB", f"{a_free_ram} MB", f"{free_sign} MB"),
            "├────────────────────────────────────────────────────────────────────────┤",
            note("Scope: user-0 packages + settings only; APKs stay in /system."),
            note(f"Available RAM gain: {ram_freed_hdr} MB (total minus used, dumpsys PSS)."),
        ]
    )
    if actions and actions.get("actions"):
        reversible = sum(1 for a in actions["actions"] if (a.get("restore") or "").strip())
        card += "\n" + note(f"Action log: {len(actions['actions'])} recorded, {reversible} reversible.")
        card += "\n" + note("Reversal: bash ./backups/restore.sh")
    else:
        card += "\n" + note("Action log: none - only the snapshot diff above is proven.")
    card += "\n└────────────────────────────────────────────────────────────────────────┘"
    print(card)

    if removed_packages:
        print(f"[*] Top Decommissioned Packages ({len(removed_packages)} total):")
        for pkg in removed_packages[:15]:
            print(f"    - {pkg}")
        if len(removed_packages) > 15:
            print(f"    ... and {len(removed_packages) - 15} more.")

    # Write HTML report
    html_report_path = BACKUPS_DIR / "report.html"
    generate_html_report(before_data, after_data, diff, html_report_path, actions=actions)
    print("\n[+] Interactive Dark-Mode HTML Report generated at:")
    print(f"    -> {html_report_path.resolve()}\n")
    if not actions:
        print("[!] No backups/actions.json: log every change with `tools/audit.py log-action`", file=sys.stderr)
        print("    so the report and restore.sh reflect what actually ran.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="cleanyourdroid - Android ADB Audit, Telemetry & Debloat Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 tools/audit.py snapshot before
  python3 tools/audit.py log-action --kind package --target com.miui.msa.global \\
      --command "adb shell pm uninstall -k --user 0 com.miui.msa.global" \\
      --restore "adb shell cmd package install-existing com.miui.msa.global"
  python3 tools/audit.py snapshot after
  python3 tools/audit.py compare before after
  python3 tools/audit.py restore-script
""",
    )
    parser.add_argument("--adb", help="Path (or JSON argv array) to the adb binary")
    parser.add_argument("--serial", help="ADB serial of the target device")
    parser.add_argument(
        "--backups",
        default="backups",
        help="Directory for snapshots, the action log and the report (default: backups)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # snapshot command
    snap_parser = subparsers.add_parser("snapshot", help="Capture snapshot of connected device state")
    snap_parser.add_argument("label", help="Snapshot identifier (e.g. 'before' or 'after')")

    # compare command
    comp_parser = subparsers.add_parser("compare", help="Compare two snapshots and output summary")
    comp_parser.add_argument("before", help="Baseline snapshot label (e.g. 'before')")
    comp_parser.add_argument("after", help="Post-optimization snapshot label (e.g. 'after')")
    comp_parser.add_argument("--actions", help="Action log to embed in the report (default: backups/actions.json)")

    # log-action command
    log_parser = subparsers.add_parser(
        "log-action", help="Record one executed change (feeds report.html and restore.sh)"
    )
    log_parser.add_argument(
        "--kind",
        default="package",
        choices=("package", "appops", "settings", "dexopt", "cache", "other"),
        help="Category of the change (default: package)",
    )
    log_parser.add_argument("--target", required=True, help="Package name or setting key")
    log_parser.add_argument("--command", help="Exact command that was executed")
    log_parser.add_argument("--restore", help="Exact command that reverses it")
    log_parser.add_argument(
        "--result",
        default="ok",
        choices=("ok", "failed", "skipped", "already", "noop"),
        help="Outcome of the command (default: ok)",
    )
    log_parser.add_argument("--note", help="Free-form note shown in the log")
    log_parser.add_argument("--actions", help="Action log path (default: backups/actions.json)")
    log_parser.add_argument(
        "--no-device-probe",
        action="store_true",
        help="Do not query the phone for device metadata (offline use)",
    )

    # restore-script command
    restore_parser = subparsers.add_parser(
        "restore-script", help="Render backups/restore.sh from the recorded action log"
    )
    restore_parser.add_argument("--actions", help="Action log path (default: backups/actions.json)")
    restore_parser.add_argument("--output", help="Where to write the script (default: backups/restore.sh)")

    args = parser.parse_args()
    _ADB_OPTIONS.update(binary=args.adb, serial=args.serial)
    global BACKUPS_DIR
    BACKUPS_DIR = Path(args.backups)

    try:
        if args.subcommand == "snapshot":
            cmd_snapshot(args.label)
        elif args.subcommand == "compare":
            cmd_compare(args.before, args.after, args.actions)
        elif args.subcommand == "log-action":
            cmd_log_action(args)
        elif args.subcommand == "restore-script":
            sys.exit(cmd_restore_script(args))
    except RuntimeError as e:
        print(f"\n[!] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
