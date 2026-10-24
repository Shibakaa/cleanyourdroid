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
│ Active Used RAM           │ 6,788.9 MB   │ 6,133.0 MB   │ -655.9 MB    │
│ Available Memory Buffer   │ 9,305.8 MB   │ 9,121.4 MB   │ -184.4 MB    │
├────────────────────────────────────────────────────────────────────────┤
│ Status: 100% Rootless Clean & Optimized                                │
│ Active RAM Gain: +655.9 MB freed from background services              │
│ Reversibility: Ready via ./backups/restore.sh                          │
└────────────────────────────────────────────────────────────────────────┘
```

> **Пример интерактивного отчета:** Ознакомьтесь с [`assets/sample-report.html`](assets/sample-report.html) &mdash; готовым темным bento-дашбордом, сгенерированным на основе реальной телеметрии POCO F5.

---

## Как это работает

| Этап | Действие | Описание |
|:---:|:---|:---|
| **1** | **Бэкап и снапшот** | Снятие базовых метрик ОЗУ и установленных пакетов через `tools/audit.py`, сохранение глобальных настроек и генерация скрипта `restore.sh`. |
| **2** | **Интерактивный аудит** | Сверка списка пакетов с базами `safety/known_bloatware.json` и `safety/bootloop_blacklist.json`, вывод структурированной таблицы на подтверждение пользователю. |
| **3** | **Деблоатинг и ART** | Отключение подтвержденного мусора (с сохранением данных `-k`), ограничение фонового жора батареи (`appops`), очистка кэша и компиляция `bg-dexopt-job`. |
| **4** | **Отчет и бенчмарк** | Формирование сводной карточки в консоли и создание интерактивного темного HTML-дашборда в `./backups/report.html`. |

---

## Быстрый старт

### 1. Подготовка
- Компьютер с **Python 3.8+** и **ADB** ([Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)).
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

---

## Гарантия безопасности и защита от бутлупов

В отличие от скриптов, удаляющих всё вслепую:
1. **Защита от окирпичивания:** Каждый пакет проверяется по черному списку [`safety/bootloop_blacklist.json`](safety/bootloop_blacklist.json). Критические компоненты (`com.miui.securitycenter`, `com.xiaomi.finddevice`, `com.miui.powerkeeper`, ядро Knox, `SystemUI`, клавиатуры и службы телефонии) защищены от изменений на уровне правил агента.
2. **Без потери данных (флаг `-k`):** Системные приложения удаляются командой `pm uninstall -k --user 0`. Сам APK остается в системном разделе `/system`, а пользовательские данные и кэш не стираются.
3. **Мгновенный откат в один клик:** Каждая модификация автоматически фиксирует команду восстановления в файле `./backups/restore.sh`:
   ```bash
   # Восстановить все удаленные приложения в любой момент:
   bash ./backups/restore.sh
   ```

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

### 3. Оптимизация оперативной памяти и системы
- Ограничение прожорливых фоновых приложений через `adb shell cmd appops set <pkg> RUN_IN_BACKGROUND ignore`.
- Сброс неиспользуемого системного кэша: `adb shell pm trim-caches 999G`.
- Запуск профильной Ahead-of-Time компиляции байткода ART для оставшихся приложений: `adb shell cmd package bg-dexopt-job`.

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
| **Google** | Pixel 7 / 8 / 9 Series | `panther` / `shiba` / `caiman` | Pixel UI (Android 14 / 15) | ⚠️ **Не тестировалось** | *Приветствуется PR* |
| **Realme / Oppo** | GT / Find Series | Различные | ColorOS 14 (Android 14) | ⚠️ **Не тестировалось** | *Приветствуется PR* |

### Добавьте профиль вашего устройства
Оптимизировали свой смартфон с помощью `cleanyourdroid`? Создайте Pull Request с профилем вашего устройства в папке `devices/<brand>/<codename>.md`, чтобы помочь другим пользователям!

---

## Структура репозитория

```
cleanyourdroid/
├── AGENTS.md                  # Главные инструкции для AI-агентов
├── GEMINI.md                  # Инструкции для Gemini CLI
├── CLAUDE.md                  # Инструкции для Claude Code
├── PROMPT.md                  # 4-этапный интерактивный промпт для пользователя
├── README.md                  # Документация на английском
├── README.ru.md               # Документация на русском
├── safety/
│   ├── bootloop_blacklist.json # Черный список критических системных пакетов
│   └── known_bloatware.json    # База проверенного мусора и трекеров
├── tools/
│   └── audit.py               # Утилита аудита ОЗУ и генерации HTML-отчета
└── devices/
    └── xiaomi/
        └── poco-f5-marble.md  # Эталонный профиль POCO F5
```

---

## Утилита аудита и телеметрии (`tools/audit.py`)

Вы можете использовать инструмент на стандартной библиотеке Python без внешних зависимостей отдельно:

```bash
# Сделать снимок состояния ДО очистки:
python3 tools/audit.py snapshot before

# Сделать снимок состояния ПОСЛЕ очистки:
python3 tools/audit.py snapshot after

# Сравнить снимки, вывести карточку в консоль и сгенерировать HTML-дашборд:
python3 tools/audit.py compare before after
```

Файл `./backups/report.html` представляет собой автономный темный bento-дашборд, готовый для публикации на Reddit, X или в Telegram.

---

## Лицензия

Проект распространяется под открытой лицензией [MIT License](LICENSE).  
*Создано с вдохновением от [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).*
