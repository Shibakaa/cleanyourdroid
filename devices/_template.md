# <Brand> <Model> (`<codename>`) &bull; <OS and version> profile

Copy this file to `devices/<brand>/<codename>.md` and replace every placeholder.
Delete the rows you did not test; an honest short profile beats a long guess.

---

## 1. Device metadata

| Parameter | Specification |
|:---|:---|
| **Commercial model** | |
| **Device codename** | |
| **System on Chip** | |
| **Memory / storage** | |
| **Verified OS build** | |
| **Target architecture** | `arm64-v8a` |

## 2. Prerequisites

Any extra toggles this device needs beyond "USB debugging" (Xiaomi security settings, ColorOS permission monitoring, ...).

## 3. Verified removals

| Package | App name | Why it is safe here | Reverted? |
|:---|:---|:---|:---:|
| `com.example.bloat` | | | no |

## 4. Restrictions instead of removal

| Package | What was applied | Effect |
|:---|:---|:---|
| `com.example.app` | `am set-standby-bucket restricted` | |

## 5. Packages kept for stability

Anything that *looks* like bloat but broke something when removed. This is the most valuable section of the file.

| Package | What broke |
|:---|:---|

## 6. Measurements

| Metric | Before | After | Delta |
|:---|:---:|:---:|:---:|
| Enabled packages (user 0) | | | |
| Used RAM (dumpsys PSS) | | | |
| Available RAM (total − used) | | | |

Snapshots: attach the `before.json` / `after.json` numbers, not the files.

## 7. Notes

Anything that misbehaved after the session, even if you reverted it.
