#!/usr/bin/env python3
"""A tiny stand-in for `adb`, used by the test suite and for offline demos.

It answers the handful of commands cleanyourdroid actually issues, so
``audit.py`` and ``plan.py`` can be exercised on a machine with no phone
attached (CI included).

Usage
-----
    set CLEANYOURDROID_ADB=["C:/Python312/python.exe", "tests/fake_adb.py"]
    set FAKE_CYD_STATE=before        # or "after"
    python3 tools/audit.py snapshot before
    python3 tools/plan.py

Error paths:
    set FAKE_CYD_FAIL=unauthorized   -> `adb devices` reports an unauthorized phone
    set FAKE_CYD_FAIL=none           -> no devices attached
    set FAKE_CYD_FAIL=multiple       -> two phones attached, no --serial given
"""

from __future__ import annotations

import os
import sys

SERIAL = "FAKE0CLEAN"

BASE_PACKAGES = [
    # Android / Google core (must never be proposed)
    "android",
    "com.android.systemui",
    "com.android.settings",
    "com.android.phone",
    "com.android.providers.telephony",
    "com.android.providers.media",
    "com.android.packageinstaller",
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.google.android.packageinstaller",
    "com.google.android.permissioncontroller",
    "com.google.android.inputmethod.latin",
    "com.android.vending",
    # OEM / system packages that are protected on Xiaomi
    "com.miui.securitycenter",
    "com.miui.powerkeeper",
    "com.xiaomi.finddevice",
    "com.xiaomi.xmsf",
    "com.mi.android.globallauncher",
    "com.miui.home",
    "com.miui.securityadd",
    "com.miui.guardprovider",
    # Bloat that the database knows about
    "com.miui.msa.global",
    "com.miui.analytics",
    "com.miui.bugreport",
    "com.miui.Hybrid",
    "com.miui.hybrid.accessory",
    "com.aura.oobe.xiaomi",
    "com.ironsource.aura.xiaomi",
    "com.facebook.system",
    "com.facebook.appmanager",
    "com.facebook.services",
    "com.xiaomi.mipicks",
    "com.mi.globalbrowser",
    "com.xiaomi.glgm",
    "com.miui.yellowpage",
    "com.miui.videoplayer",
    "com.miui.player",
    "com.xiaomi.payment",
    "com.mipay.wallet.in",
    "com.miui.cleanmaster",
    "com.miui.android.fashiongallery",
    # Regional preloads
    "ru.vk.store",
    "ru.yandex.searchplugin",
    "com.yandex.browser",
    "com.vkontakte.android",
    "ru.mail.mailapp",
    "com.kms.free",
    # Plain user apps
    "com.instagram.android",
    "org.telegram.messenger",
    "com.zhiliaoapp.musically",
]

REMOVED_IN_AFTER = [
    "com.miui.msa.global",
    "com.miui.analytics",
    "com.miui.bugreport",
    "com.facebook.system",
    "com.facebook.appmanager",
    "com.facebook.services",
    "com.xiaomi.mipicks",
    "com.mi.globalbrowser",
    "com.xiaomi.glgm",
    "com.miui.yellowpage",
    "com.miui.videoplayer",
    "com.miui.player",
    "com.xiaomi.payment",
    "com.miui.android.fashiongallery",
    "com.miui.Hybrid",
]

PROPS = {
    "ro.product.brand": "Xiaomi",
    "ro.product.model": "POCO F5",
    "ro.product.device": "marble",
    "ro.build.version.release": "15",
    "ro.build.display.id": "HyperOS 3.0.2.0.VMRRUXM",
    "ro.build.version.security_patch": "2025-09-01",
    "ro.soc.model": "Qualcomm Snapdragon 7+ Gen 2",
    "ro.board.platform": "kalama",
}

MEMINFO = {
    "before": """Applications Memory Usage (in Kilobytes):
Uptime: 4821934 Realtime: 4821934

Total PSS by process:
    512,600K: com.android.systemui (pid 1823)
    402,300K: com.miui.home (pid 2911)
    344,800K: com.facebook.katana (pid 5110)
    298,100K: com.android.chrome (pid 4302)
    187,600K: com.miui.securitycenter (pid 2201)
    120,900K: ru.yandex.searchplugin (pid 6012)

Total PSS by OOM adjustment:
    512,600K: Native
    402,300K: Persistent

Total RAM: 11,160,000K (0K free)
 Free RAM: 9,305,800K (4,600,600K cached pss + 3,000,000K cached kernel + 1,705,200K free)
 Used RAM: 6,788,900K (4,900,000K used pss + 1,888,900K kernel)
 Lost RAM: 45,300K
   ZRAM: 1,813,400K physical used for 3,901,000K in swap (2,048,000K total swap)
""",
    "after": """Applications Memory Usage (in Kilobytes):
Uptime: 4855910 Realtime: 4855910

Total PSS by process:
    508,900K: com.android.systemui (pid 1823)
    398,700K: com.miui.home (pid 2911)
    301,400K: com.android.chrome (pid 5120)
    188,200K: com.miui.securitycenter (pid 2201)

Total PSS by OOM adjustment:
    508,900K: Native
    398,700K: Persistent

Total RAM: 11,160,000K (0K free)
 Free RAM: 9,121,400K (4,445,800K cached pss + 3,000,000K cached kernel + 1,675,600K free)
 Used RAM: 6,133,000K (4,300,000K used pss + 1,833,000K kernel)
 Lost RAM: 44,100K
   ZRAM: 1,772,000K physical used for 3,812,000K in swap (2,048,000K total swap)
""",
}

PROC_MEMINFO = {
    "before": """MemTotal:       11427840 kB
MemFree:         1746124 kB
MemAvailable:    4371000 kB
Buffers:           98112 kB
Cached:          1980000 kB
SwapTotal:       2097152 kB
SwapFree:         320000 kB
""",
    "after": """MemTotal:       11427840 kB
MemFree:         1715320 kB
MemAvailable:    5027000 kB
Buffers:           97400 kB
Cached:          1854000 kB
SwapTotal:       2097152 kB
SwapFree:         280000 kB
""",
}


def state():
    return os.environ.get("FAKE_CYD_STATE", "before").strip().lower()


def packages():
    override = os.environ.get("FAKE_CYD_PACKAGES")
    if override and os.path.isfile(override):
        with open(override, "r", encoding="utf-8") as handle:
            names = [line.strip() for line in handle if line.strip()]
    elif state() == "after":
        names = [p for p in BASE_PACKAGES if p not in REMOVED_IN_AFTER]
    else:
        names = list(BASE_PACKAGES)
    return sorted(set(names))


def disabled_packages():
    return []


def emit(text=""):
    sys.stdout.write(text if text.endswith("\n") or not text else text + "\n")


def handle(args):
    fail = os.environ.get("FAKE_CYD_FAIL", "").strip().lower()

    if args[:1] == ["devices"]:
        if fail == "none":
            emit("List of devices attached\n")
            return 0
        if fail == "unauthorized":
            emit("List of devices attached\n%s\tunauthorized\n" % SERIAL)
            return 0
        if fail == "multiple":
            emit("List of devices attached\n%s\tdevice product:marble model:POCO_F5\nOTHER0DEVICE\tdevice\n" % SERIAL)
            return 0
        emit("List of devices attached\n%s\tdevice product:marble model:POCO_F5 device:marble\n" % SERIAL)
        return 0

    if args[:1] == ["get-serialno"]:
        emit(SERIAL)
        return 0

    if args[:1] == ["shell"]:
        return handle_shell(args[1:])

    emit("")
    return 0


def handle_shell(args):
    if args[:1] == ["getprop"]:
        emit(PROPS.get(args[1] if len(args) > 1 else "", ""))
        return 0

    if args[:2] == ["dumpsys", "meminfo"]:
        emit(MEMINFO.get(state(), MEMINFO["before"]))
        return 0

    if args[:2] == ["cat", "/proc/meminfo"]:
        emit(PROC_MEMINFO.get(state(), PROC_MEMINFO["before"]))
        return 0

    if args[:2] == ["pm", "list"]:
        mode = ""
        for token in args:
            if token in ("-e", "-d", "--disabled", "--enabled"):
                mode = token
        if mode in ("-d", "--disabled"):
            names = disabled_packages()
        else:
            names = packages()
        emit("\n".join("package:%s" % name for name in names))
        return 0

    emit("")
    return 0


def main():
    args = sys.argv[1:]
    if args[:2] == ["-s", SERIAL] or (args and args[0] == "-s"):
        args = args[2:]
    return handle(args)


if __name__ == "__main__":
    sys.exit(main())
