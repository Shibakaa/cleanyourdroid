<div align="center">

# cleanyourdroid

**Ваш Android-смартфон без рекламы, спама и слежки.**  
Деблоатинг и глубокая оптимизация любого Android-устройства через ADB с помощью вашего AI-агента.

[English](README.md) &bull; [Русская версия](README.ru.md)

<br/>

[![License: MIT](https://img.shields.io/badge/Лицензия-MIT-10b981.svg)](LICENSE)
[![Платформа](https://img.shields.io/badge/Платформа-Android%20%7C%20HyperOS%20%7C%20OneUI-38bdf8.svg?logo=android&logoColor=white)](https://developer.android.com)
[![Root](https://img.shields.io/badge/Root-Не%20требуется%20(100%25%20Rootless)-emerald.svg)](#гарантия-безопасности-и-защита-от-бутлупов)
[![PRs Welcome](https://img.shields.io/badge/PRs-Приветствуются-indigo.svg)](https://github.com/Shibakaa/cleanyourdroid/pulls)
[![Протестировано](https://img.shields.io/badge/Флагман-POCO%20F5%20(marble)-f43f5e.svg)](devices/xiaomi/poco-f5-marble.md)

</div>

---

Современные смартфоны от Xiaomi, Samsung, BBK (OnePlus/Realme/Oppo) и даже Google поставляются с колоссальным объемом фоновой телеметрии, рекламой на экранах блокировки, партнерскими приложениями и скрытыми автоустановщиками APK.

`cleanyourdroid` превращает вашего AI-ассистента (Claude Code, Gemini CLI, Cursor, Windsurf, Codex) в квалифицированного Android-инженера. Подключите телефон по USB или беспроводной отладке, отправьте агенту `PROMPT.md`, и он проведет аудит, очистит устройство от мусора, ограничит фоновые службы и скомпилирует профили ART &mdash; без root-прав и с возможностью мгновенного восстановления в один клик.

Агент не придумывает пакеты по памяти: детерминированный планировщик сверяет установленные пакеты с двумя базами, а каждое действие логируется. Поэтому отчёт и скрипт восстановления физически не могут разойтись с тем, что реально выполнялось.

---

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CLEANYOURDROID OPTIMIZATION REPORT                │
├────────────────────────────────────────────────────────────────────────┤
│ Device:           Xiaomi POCO F5 (marble)                              │
│ OS & Build:       Android 15 (HyperOS 3.0.2.0.VMRRUXM)                 │
│ Chipset / SoC:    Qualcomm Snapdragon 7+ Gen 2 (SM7475)                │
├────────────────────────────────────────────────────────────────────────┤
│ METRIC                    │ BEFORE       │ AFTER        │ DELTA        │
├───────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Enabled Packages          │ 731          │ 716          │ -15          │
│ Used RAM (PSS)            │ 6788.9 MB    │ 6133.0 MB    │ -655.9 MB    │
│ Available RAM             │ 4371.1 MB    │ 5027.0 MB    │ +655.9 MB    │
│ Free RAM (incl. cache)    │ 9305.8 MB    │ 9121.4 MB    │ -184.4 MB    │
├────────────────────────────────────────────────────────────────────────┤
│ Scope: user-0 packages + settings only; APKs stay in /system.          │
│ Available RAM gain: +655.9 MB (total minus used, dumpsys PSS).         │
│ Action log: 23 recorded, 23 reversible.                                │
│ Reversal: bash ./backups/restore.sh                                    │
└────────────────────────────────────────────────────────────────────────┘
```

> **Пример интерактивного отчета:** Ознакомьтесь с [`assets/sample-report.html`](assets/sample-report.html) &mdash; готовым темным bento-дашбордом, сгенерированным на основе реальной телеметрии POCO F5.

---

## Как это работает

| Этап | Действие | Описание |
|:---:|:---|:---|
| **1** | **Снимок и бэкап** | `tools/audit.py snapshot before` фиксирует ОЗУ, пакеты и топ-процессы; списки пакетов и настроек сохраняются в `backups/`. |
| **2** | **Детерминированный план** | `tools/plan.py` сверяет установленные пакеты с `safety/known_bloatware.json` и отбрасывает всё из `safety/bootloop_blacklist.json`. Агент показывает именно эту таблицу, а не список из памяти. |
| **3** | **Выполнение и лог** | Каждое подтвержденное изменение сразу пишется в `tools/audit.py log-action` вместе с точной командой откатa. |
| **4** | **Тюнинг** | Standby-бакеты, анимации, рекламные флаги оболочки, очистка кэшей и компиляция ART &mdash; всё опционально и всё логируется. |
| **5** | **Отчёт и откат** | `compare` печатает карточку и собирает `backups/report.html`; `restore-script` перегенерирует `backups/restore.sh` из лога. |

---

## Быстрый старт

### 1. Подготовка
- Компьютер с **Python 3.8+** и **ADB** ([Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)). Без pip и virtualenv: только стандартная библиотека.
- Любой AI-агент для разработки: [Claude Code](https://claude.ai/code), [Gemini CLI](https://github.com/google-gemini), [Cursor](https://cursor.sh) или [Windsurf](https://codeium.com/windsurf).

### 2. Включение параметров разработчика на смартфоне
Подключите телефон кабелем USB к компьютеру и настройте параметры разработчика:

<details>
<summary><b>Xiaomi / POCO / Redmi (HyperOS и MIUI) &mdash; ВАЖНО!</b></summary>

1. **Настройки &rarr; О телефоне** &rarr; нажмите на пункт **Версия ОС** 7 раз.
2. **Настройки &rarr; Расширенные настройки &rarr; Для разработчиков**.
3. Включите **Отладка по USB**.
4. Включите **Отладка по USB (Настройки безопасности)**. *(Требуется вставленная SIM-карта и активный аккаунт Mi. Без этого пункта команды ADB будут возвращать `SecurityException`).*
</details>

<details>
<summary><b>Samsung Galaxy (One UI)</b></summary>

1. **Настройки &rarr; Сведения о телефоне &rarr; Сведения о ПО** &rarr; нажмите на **Номер сборки** 7 раз.
2. **Настройки &rarr; Параметры разработчика** &rarr; включите **Отладка по USB**.
</details>

<details>
<summary><b>Google Pixel / Motorola / Sony (AOSP / Pixel UI)</b></summary>

1. **Настройки &rarr; О телефоне** &rarr; нажмите на **Номер сборки** 7 раз.
2. **Настройки &rarr; Система &rarr; Для разработчиков** &rarr; включите **Отладка по USB**.
</details>

<details>
<summary><b>Realme / OnePlus / Oppo (ColorOS / OxygenOS)</b></summary>

1. **Настройки &rarr; Об устройстве &rarr; Версия** &rarr; нажмите на **Номер сборки** 7 раз.
2. **Настройки &rarr; Дополнительные настройки &rarr; Для разработчиков** &rarr; включите **Отладка по USB**.
3. Отключите пункт **Мониторинг разрешений**, если команды ADB вызывают запросы подтверждения.
</details>

### 3. Запуск агента
Откройте папку репозитория в вашем AI-агенте и отправьте содержимое файла [`PROMPT.md`](PROMPT.md):

```bash
# Пример с Claude Code:
claude
# Вставьте текст из PROMPT.md
```

```bash
# Пример с Gemini CLI:
gemini
# Вставьте текст из PROMPT.md
```

Агент проведет проверку, предоставит таблицу предлагаемых к удалению программ и будет ждать вашего согласия перед внесением изменений.

### 4. Или просто посмотреть план (без агента и без риска)
```bash
python3 tools/plan.py            # что будет удалено именно на этом телефоне
python3 tools/plan.py --format md
python3 tools/plan.py --validate # проверка самих баз
```
`plan.py` работает только на чтение: устройство он не меняет.

---

## Гарантия безопасности и защита от бутлупов

В отличие от скриптов, удаляющих всё вслепую:
1. **Детерминированная защита:** `tools/plan.py` исключает всё, что перечислено в [`safety/bootloop_blacklist.json`](safety/bootloop_blacklist.json), ещё до того, как агент увидит список кандидатов, и показывает, сколько защищённых пакетов установлено &mdash; это видимое доказательство, что фильтр работает. Критические компоненты (`com.miui.securitycenter`, `com.xiaomi.finddevice`, `com.miui.powerkeeper`, ядро Knox, `SystemUI`, звонилка, активные клавиатура и лаунчер) защищены.
2. **Никаких выдуманных имён пакетов:** кандидаты на удаление &mdash; только записи [`safety/known_bloatware.json`](safety/known_bloatware.json), которые реально установлены. Всё остальное требует отдельного подтверждения с проверкой идентификатора.
3. **Без потери данных (флаг `-k`):** системные приложения удаляются командой `pm uninstall -k --user 0`. Сам APK остаётся в `/system`, данные приложения тоже.
4. **Проверка выполнения:** после каждой партии выполняется `pm list packages -e --user 0` и `dumpsys window`, чтобы сразу поймать циклический краш SystemUI.
5. **Мгновенный откат:** каждое изменение фиксируется вместе с точной командой откатa в `backups/actions.json`, а `backups/restore.sh` генерируется из этого лога:
   ```bash
   # Восстановить всё, начиная с последнего изменения:
   bash ./backups/restore.sh
   # Указать конкретное устройство, если подключено несколько:
   ADB="adb -s <serial>" bash ./backups/restore.sh
   ```

> [!NOTE]
> `pm uninstall -k --user 0` освобождает **ОЗУ и фоновую активность, но не память накопителя**: APK остаётся в системном разделе, а `-k` сохраняет данные. Место освобождает только `pm trim-caches` (кэши). Раньше README намекал на обратное &mdash; исправлено.

---

## Что удаляется и оптимизируется

### 1. Реклама, трекеры и телеметрия
- **Xiaomi / POCO:** `com.miui.msa.global` (системная реклама MIUI), `com.miui.analytics`, `com.miui.bugreport`, `com.miui.Hybrid` (шлюз рекламы Quick Apps), `com.aura.oobe.xiaomi` (Digital Turbine / партнерские загрузки), `com.ironsource.aura.xiaomi`.
- **Samsung:** `com.samsung.android.app.spage` (рекламный экран Samsung Free), `com.samsung.android.rubin.app` (служба таргетинга Customization Service).
- **Универсальные пакеты:** Системные службы Meta/Facebook (`com.facebook.system`, `com.facebook.appmanager`, `com.facebook.services`).

### 2. Предустановленный партнерский софт и спам
- `com.miui.android.fashiongallery` (Карусель обоев с рекламой на экране блокировки)
- `com.mi.globalbrowser` (Mi Браузер со встроенным трекингом)
- `com.xiaomi.glgm` (Реклама игр Game Center)
- `com.miui.yellowpage` (Желтые страницы / реклама в звонилке)
- `com.miui.videoplayer` и `com.miui.player` (Медиаплееры со спам-уведомлениями)
- `com.xiaomi.mipicks` (Магазин GetApps с навязчивыми загрузками)
- `com.samsung.android.bixby.agent` (Фоновый сервис ассистента Bixby)

### 3. Google Pixel / AOSP
Здесь нет рекламных SDK вендора. Категория `google_pixel` перечисляет предустановленные приложения, по которым нужно решение: Pixel Tips (можно смело убирать), YouTube / YouTube Music / Photos / Chrome / Gemini / Digital Wellbeing / Personal Safety (на ваше усмотрение). Телеметрию Google (`com.google.android.gms`, `com.google.android.gsf`) без root убрать нельзя, и инструмент не делает вид, что может.

### 4. Оптимизация оперативной памяти и системы
- Ограничение тяжёлых сторонних приложений через App Standby (`am set-standby-bucket <pkg> restricted`) и, по вашему запросу, через AppOps (`cmd appops set <pkg> RUN_IN_BACKGROUND ignore` &mdash; это **может** отключить уведомления).
- Сброс кэшей пакетов: `pm trim-caches 999G`.
- Профильная AOT-компиляция: `cmd package bg-dexopt-job` или `cmd package compile -m speed-profile -f <pkg>` для отдельных приложений.

---

## Матрица совместимости устройств и ОС

> [!IMPORTANT]
> Имена пакетов, фоновые службы и разрешения AppOps различаются в зависимости от оболочки вендора и мажорной версии Android. **Только конфигурации со статусом `✅ Протестировано` были проверены на реальном физическом устройстве с полными логами телеметрии «до» и «после».**
> Для конфигураций со статусом `⚠️ Не тестировалось` агент действует максимально консервативно, опираясь на черный список `safety/bootloop_blacklist.json` и интерактивное подтверждение пользователя. Мы приветствуем Pull Request'ы сообщества для расширения базы проверенных профилей!

| Бренд / Вендор | Семейство моделей | Кодовое имя | Оболочка и версия Android | Статус тестирования | Профиль и замеры |
|:---|:---|:---|:---|:---:|:---:|
| **Xiaomi / POCO** | **POCO F5 / Redmi Note 12 Turbo** | `marble` / `marblein` | **HyperOS 3.0** (Android 15) и **HyperOS 1.0** (Android 14) | ✅ **Протестировано** | [Смотреть замеры в железе](devices/xiaomi/poco-f5-marble.md) |
| **Samsung** | Galaxy S23 / S24 Series | `kalama` / `pineapple` | One UI 6.x / 7.x (Android 14 / 15) | ⚠️ **Не тестировалось** | *Приветствуется PR* |
| **OnePlus** | OnePlus 11 / 12 | `salami` / `pineapple` | OxygenOS 14 / 15 (Android 14 / 15) | ⚠️ **Не тестировалось** | *Приветствуется PR* |
| **Google** | Pixel 7 / 8 / 9 / 10 Series | `panther` / `shiba` / `caiman` | Pixel UI (Android 14 - 16) | ⚠️ **Не тестировалось** | *Рекламы вендора нет: 1-2 безопасных удаления* |
| **Realme / Oppo** | GT / Find Series | Различные | ColorOS 14 (Android 14) | ⚠️ **Не тестировалось** | *Приветствуется PR* |

### Добавьте профиль вашего устройства
Оптимизировали свой смартфон с помощью `cleanyourdroid`? Создайте Pull Request с профилем вашего устройства в папке `devices/<brand>/<codename>.md`, чтобы помочь другим пользователям!

---

## FAQ

**«Что будет удалено на моём телефоне?»**
Запустите `python3 tools/plan.py` &mdash; он покажет именно это, сгруппировав по риску, на основе баз в `safety/`. На Pixel 10 Pro XL честный ответ: *Pixel Tips плюс список предустановленных Google-приложений на ваше усмотрение* &mdash; на Pixel нет ни MSA, ни Digital Turbine, ни установщиков Meta. Данные по Pixel в репозитории иллюстративные, а не проверенный профиль; PR с реального устройства очень приветствуется.

**«Почему одна из цифр стала меньше после очистки?»**
`Free RAM` из `dumpsys` включает кэш, поэтому она колеблется вместе с давлением на кэш. Реальный запас памяти &mdash; это `Available RAM` (всего минус занято). Печатаются обе цифры, чтобы арифметику можно было проверить.

**«Это ломает гарантию / Knox / OTA?»**
Нет root, нет разблокировки загрузчика, нет изменения системного раздела: пакеты скрываются только для пользователя 0, а настройки меняются через официальный провайдер `settings`. Сброс к заводским настройкам возвращает всё, а `restore.sh` делает то же без сброса.

---

## Структура репозитория

```
cleanyourdroid/
├── AGENTS.md                  # Главные инструкции для AI-агентов
├── CLAUDE.md                  # Точка входа Claude Code (ссылается на AGENTS.md)
├── GEMINI.md                  # Точка входа Gemini CLI (ссылается на AGENTS.md)
├── PROMPT.md                  # 5-этапный интерактивный промпт для пользователя
├── README.md                  # Документация на английском
├── README.ru.md               # Документация на русском
├── safety/
│   ├── bootloop_blacklist.json # Черный список критических системных пакетов
│   └── known_bloatware.json    # База проверенного мусора и трекеров
├── tools/
│   ├── adbkit.py              # Общий слой ADB (выбор устройства, ошибки)
│   ├── audit.py               # Снимки, лог действий, скрипт откатa, HTML-отчёт
│   └── plan.py                # Детерминированный план по обеим базам
├── tests/
│   ├── fake_adb.py            # Заглушка adb, чтобы тесты шли без телефона
│   └── test_tools.py          # Сквозные тесты (python -m unittest discover -s tests)
└── devices/
    └── xiaomi/
        └── poco-f5-marble.md  # Эталонный профиль POCO F5
```

---

## Инструменты

### `tools/plan.py` &mdash; что будет удалено?
```bash
python3 tools/plan.py                 # группы в консоли
python3 tools/plan.py --format md     # таблица Markdown для чата или PR
python3 tools/plan.py --format json   # структурированный вывод для скриптов и агентов
python3 tools/plan.py --validate      # проверка баз на дубликаты и пересечения
python3 tools/plan.py --packages-file backups/installed_packages_before.txt  # офлайн
```

### `tools/audit.py` &mdash; телеметрия, лог действий, отчёт
```bash
python3 tools/audit.py snapshot before
python3 tools/audit.py log-action --kind package --target com.miui.msa.global \
  --command "adb shell pm uninstall -k --user 0 com.miui.msa.global" \
  --restore "adb shell cmd package install-existing com.miui.msa.global" --result ok
python3 tools/audit.py snapshot after
python3 tools/audit.py restore-script     # перегенерировать backups/restore.sh из лога
python3 tools/audit.py compare before after
```

Файл `./backups/report.html` представляет собой автономный темный bento-дашборд, который утверждает только то, что было измерено или залогировано.

### Запуск тестов
```bash
python -m unittest discover -s tests -v
```
Телефон не нужен: `tests/fake_adb.py` отвечает на `getprop`, `dumpsys meminfo` и `pm list packages`. Любую другую обёртку adb можно подключить через `CLEANYOURDROID_ADB`.

---

## Лицензия

Проект распространяется под открытой лицензией [MIT License](LICENSE).  
*Создано с вдохновением от [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).*
