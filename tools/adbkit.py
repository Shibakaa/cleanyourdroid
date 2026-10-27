#!/usr/bin/env python3
"""Shared ADB plumbing for the cleanyourdroid tools.

One place for binary discovery, device selection and user-facing error
messages, so ``audit.py`` and ``plan.py`` always talk to the phone the same
way. Zero external dependencies (Python 3.10+ stdlib only).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_TIMEOUT = 20


class AdbError(RuntimeError):
    """ADB cannot be used: missing binary, no device, or an unusable device."""


def repo_root() -> Path:
    """Repository root: the parent of the directory that holds this file."""
    return Path(__file__).resolve().parent.parent


def _command_from_value(raw):
    """Accept either a plain path or a JSON argv array.

    The JSON form exists so Windows paths with spaces work without shell
    quoting games, e.g.::

        CLEANYOURDROID_ADB='["C:\\\\Python312\\\\python.exe", "tests/fake_adb.py"]'
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.startswith("["):
        try:
            parts = json.loads(raw)
        except ValueError:
            # Not valid JSON (an unescaped Windows path, say) - use it verbatim.
            return [raw]
        return [str(part) for part in parts] if parts else None
    return [raw]


def resolve_adb_binary(explicit=None):
    """Return the argv prefix used to invoke adb, or ``None`` when not found."""
    if explicit:
        return _command_from_value(explicit)

    for variable in ("CLEANYOURDROID_ADB", "CYD_ADB"):
        command = _command_from_value(os.environ.get(variable))
        if command:
            return command

    found = shutil.which("adb")
    if found:
        return [found]

    root = repo_root()
    for candidate in (
        root / "tools" / "platform-tools" / "adb.exe",
        root / "tools" / "platform-tools" / "adb",
        root / "platform-tools" / "adb.exe",
        root / "platform-tools" / "adb",
    ):
        if candidate.is_file():
            return [str(candidate)]

    for variable in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        sdk = os.environ.get(variable)
        if not sdk:
            continue
        name = "adb.exe" if os.name == "nt" else "adb"
        candidate = Path(sdk) / "platform-tools" / name
        if candidate.is_file():
            return [str(candidate)]

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidate = Path(local_appdata) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        if candidate.is_file():
            return [str(candidate)]

    return None


class Adb:
    """Thin ADB client bound to exactly one device.

    * device selection is cached, so ``-s <serial>`` is passed only when needed;
    * a single connected phone is picked automatically;
    * two connected phones (USB + Wireless Debugging is the usual culprit)
      raise a readable error instead of failing every later command.
    """

    def __init__(self, binary=None, serial=None, timeout=DEFAULT_TIMEOUT):
        self.base = resolve_adb_binary(binary)
        if not self.base:
            raise AdbError(
                "adb was not found. Install Android Platform Tools and put adb on PATH,\n"
                "or drop the binaries into tools/platform-tools/."
            )
        self._serial = (serial or os.environ.get("ANDROID_SERIAL") or "").strip()
        self._selected = bool(self._serial)
        self.timeout = timeout

    # ------------------------------------------------------------------ raw

    def _raw(self, args, timeout=None):
        """Run adb without device selection. Returns CompletedProcess or None."""
        command = list(self.base) + list(args)
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
            )
        except FileNotFoundError:
            raise AdbError("adb could not be started: %s" % self.base[0])
        except subprocess.TimeoutExpired:
            print(
                "[!] adb timed out after %ss: %s" % (timeout or self.timeout, " ".join(args)),
                file=sys.stderr,
            )
            return None

    @staticmethod
    def _raise_for_stderr(proc):
        message = (proc.stderr or "").strip()
        lowered = message.lower()
        if "more than one device" in lowered:
            raise AdbError(
                "More than one device is connected. Pass --serial <serial> "
                "(see `adb devices -l`) or set the ANDROID_SERIAL variable."
            )
        if "device unauthorized" in lowered:
            raise AdbError(
                "Device is unauthorized. Unlock the phone and tap "
                "'Always allow from this computer' in the RSA prompt."
            )
        if "no devices/emulators found" in lowered or "device offline" in lowered:
            raise AdbError(
                "No usable Android device found. Connect it over USB or Wireless "
                "Debugging and make sure USB debugging is enabled."
            )

    # -------------------------------------------------------------- devices

    def devices(self):
        """Return ``[(serial, state, details), ...]`` from ``adb devices -l``."""
        proc = self._raw(["devices", "-l"])
        if proc is None:
            raise AdbError("adb devices -l timed out")
        if proc.returncode != 0:
            raise AdbError("adb devices failed: %s" % (proc.stderr or "").strip())
        found = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices") or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                found.append((parts[0], parts[1], " ".join(parts[2:])))
        return found

    def select(self):
        """Pick the device to talk to and cache its serial."""
        devices = self.devices()
        online = [item for item in devices if item[1] == "device"]

        if self._serial:
            for serial, _state, _details in online:
                if serial == self._serial:
                    self._selected = True
                    return self._serial
            self._selected = False
            known = ", ".join(item[0] for item in devices) or "none"
            raise AdbError(
                "Device '%s' is not connected. Currently visible: %s." % (self._serial, known)
            )

        if len(online) == 1:
            self._serial = online[0][0]
            self._selected = True
            return self._serial

        if not online:
            unauthorised = [item[0] for item in devices if item[1] == "unauthorized"]
            if unauthorised:
                raise AdbError(
                    "Device %s is unauthorized. Unlock the phone and tap "
                    "'Always allow from this computer'." % ", ".join(unauthorised)
                )
            raise AdbError(
                "No Android device found. Connect the phone over USB or Wireless "
                "Debugging and enable USB debugging."
            )

        listing = ", ".join("%s (%s)" % (item[0], item[1]) for item in online)
        raise AdbError(
            "More than one device is connected: %s. Pass --serial <serial> or set "
            "ANDROID_SERIAL to choose one." % listing
        )

    @property
    def serial(self):
        if not self._selected:
            self.select()
        return self._serial

    # ---------------------------------------------------------------- calls

    def run(self, args, timeout=None):
        """Run an adb command against the selected device."""
        if not self._selected:
            self.select()
        prefix = ["-s", self._serial] if self._serial else []
        proc = self._raw(prefix + list(args), timeout=timeout)
        if proc is None:
            raise AdbError("adb timed out: %s" % " ".join(args))
        self._raise_for_stderr(proc)
        return proc

    def shell(self, args, timeout=None):
        """Run ``adb shell <args>`` and return stdout, or ``""`` on failure."""
        proc = self.run(["shell"] + list(args), timeout=timeout)
        if proc.returncode != 0:
            return ""
        return proc.stdout

    def shell_result(self, args, timeout=None):
        """Run ``adb shell <args>`` and return ``(ok, stdout, stderr)``."""
        proc = self.run(["shell"] + list(args), timeout=timeout)
        return proc.returncode == 0, proc.stdout, proc.stderr

    def getprop(self, name):
        return self.shell(["getprop", name]).strip()

    def installed_packages(self, user="0"):
        """Enabled packages for a user, sorted, without the ``package:`` prefix."""
        output = self.shell(["pm", "list", "packages", "-e", "--user", str(user)])
        return _package_lines(output)

    def disabled_packages(self, user="0"):
        output = self.shell(["pm", "list", "packages", "-d", "--user", str(user)])
        return _package_lines(output)


def _package_lines(output):
    packages = []
    for line in (output or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            name = line[len("package:"):].strip()
            if name:
                packages.append(name)
    return sorted(set(packages))
