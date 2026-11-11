# HANDOFF: мобильное управление как в Bedrock (Horizon Android)

Файл для агента, который продолжит работу. Прочитай целиком, дальше — по разделам.

## 1. Где что лежит

| Путь | Что это |
| --- | --- |
| `android-patches/0028-android-bedrock-controls.patch` | сам патч (один файл, `crates/horizon-client/src/game/touch.rs`, +222/−31) |
| `docs/agent-handoff/TOUCH-CONTROLS.md` | разбор: что взято из кода Bedrock, как включать, что осталось |
| `docs/agent-handoff/0028-android-bedrock-controls.patch` | копия патча |
| `docs/agent-handoff/android.yml.patch` | отдельный патч workflow (зашивает `HORIZON_DERIVED_URL` в APK) |
| `C:\Users\user\Desktop\Horizon Universal Launcher\horizon-derived.zip` | пакет данных для первого запуска (НЕ в git: производный от игры Mojang) |

## 2. Контекст проекта

* Android-сборка делается из порта **`Rayan-XOO/horizon`**, пин `ca93b0b765d3d2749a7b467051c31c43fcce2cf4`
  (`PORT_PINNED` в `.github/workflows/android.yml`), base versionName `0.4.5`.
* Воркфлоу `android.yml`: скачивает порт, накладывает `patches/*.patch` и `android-patches/*.patch`
  (сортировка по имени, `git apply`, неприменившийся патч просто пропускается и попадает в summary),
  собирает `packaging/android/build_apk.sh`, `versionCode = 1000 + run_number`, `versionName = <base>-os<code>`.
* Сейчас **`0025-android-friends-path.patch` и `0027-persistent-code.patch` не накладываются**
  (конфликт в `crates/horizon-client/assets/horizon/lang/en_us.json`) — это состояние на момент передачи,
  не связано с патчем 0028.
* Приложение: пакет `dev.horizonlab.horizon`, папка данных на телефоне
  `/sdcard/Android/data/dev.horizonlab.horizon/files/` (`resources/`, `horizon-derived.zip`, логи).

## 3. Что делает патч 0028

Всё — в `crates/horizon-client/src/game/touch.rs`.

| Добавлено | Где | Поведение |
| --- | --- | --- |
| `Id::FlyUp`, `Id::FlyDown` | enum `Id`, `IDS`, пресеты, `icon()`, `touch_press()` | вверх/вниз в полёте, видны только при `Game::player.flying` (`touch_flying()`), жмут `Button::South` / `Button::RightStick` |
| `Id::Action` | то же | контекстное действие (Bedrock `button.build_or_interact`), занимает слот `Mount` в Bedrock-пресете, идёт как триггер использования |
| `stick_floating`, `stick_always` | `TouchLayout`, `Touches::stick_origin`, `touch_stick`, `touch_event` | джойстик появляется под пальцем в левой половине (`x < 45%`, `y > 25%`), мёртвая зона 12 % |
| `sprint_on_movement` + двойной тап | `touch_stick`, `touch_stick_start` | стик до упора вперёд → спринт; второй тап по стику < 300 мс → спринт |
| `left_handed` | `Gui::place`, `Gui::unanchor` | зеркалит все контролы кроме `Id::Inventory` (кнопка «…» у хотбара) |
| `top_scale` | `Gui::place` | масштаб контролов с `y < 0.2` |
| `look_scale` | `touch_look()` | множитель поворота камеры пальцем (заменил три прямых вызова `self.mouse.on_move`) |
| `hold_ms` | `touch_frame`, `Ended` | «dwell before drag» — за сколько удержания начинается добыча |
| `EditAction::LeftHand/TopScale/StickFloat` | панель редактора | переключатели в редакторе раскладки (шестерёнка) |

Все новые поля `TouchLayout` имеют `#[serde(default …)]`, поэтому `touch_layout_v3.json` старых игроков
читается как раньше; `stick_floating` для старого файла берётся из пресета (Bedrock — плавающий).

## 4. Как проверить

```sh
cd <порт с наложенными патчами>

# типы (важно: mod touch НЕ под cfg(android), см. crates/horizon-client/src/game.rs:312)
cargo check -p horizon-client --lib

# полная проверка под Android
cargo check -p horizon-android --target aarch64-linux-android

# сборка APK как в CI
./packaging/android/build_apk.sh
```

Что уже проверено на момент передачи:

* `git apply --check` патча — на дереве «порт + все ваши патчи», в CRLF- и LF-вариантах (LF = как в Linux CI);
* `rustfmt --edition 2024 --emit stdout` разбирает файл без ошибок (синтаксис/скобки в порядке);
* **типы не проверены**: в песочнице, где готовился патч, не было сети для cargo (TLS schannel
  `SEC_E_NO_CREDENTIALS`, `dl.google.com` ~14 КБ/с, `static.crates.io` ~115 КБ/с) и не хватало 93 крейтов
  из `Cargo.lock` в кэше. Первым делом прогони `cargo check -p horizon-client --lib`.

## 5. Грабли, на которые уже наступали

* `Game::motion` — это `MotionResources`, а **не** `PlayerMotion`. Живой полёт:
  `self.player.as_ref().is_some_and(|p| p.flying)` (так же в `game/explosion.rs`).
* `Gui::hit()` получил 4-й аргумент `flying: bool` — обновлены все три вызова в `touch_event`.
* Добавил вариант `Id` — обнови **три** места: `IDS` (сейчас `[Id; 23]`), `icon()` (там нет `_`, матч
  должен быть исчерпывающим) и `touch_press()` (тоже без `_`).
* Плавающий стик: `Gui::hit()` его больше не ловит (проверка `stick_floating && id == Id::Stick && !editing`),
  иначе он съедал тапы в левой половине; в редакторе он по-прежнему выбирается.
* Порядок патчей: 0028 применяется последним; `0027` файл `touch.rs` не трогает, конфликта не будет.

## 6. Что осталось сделать

1. `button.block_select` — в Horizon нет аналога среднего клика в пэде.
2. `#touch_progress_bar_visible` — кольцо прогресса добычи под пальцем (нужен доступ к прогрессу ломания).
3. `ctrl_stacksplittingtriggertime` (дележ стака долгим тапом), `ctrl_swapjumpandsneak`.
4. Слайдеры в настройках для `look_scale` / `hold_ms` (пока только JSON).
5. Визуал: иконки/скругления по атласу Bedrock `textures/gui/touchgui.png` (вытащен из APK, 256×256).

## 7. Откуда взята спецификация Bedrock

* `libminecraftpe.so` из APK 1.26.40.5: RTTI-имена (`ITouchSystem`, `TouchMapper`, `TouchGlyphButtonControl`,
  `TouchTapOrHoldGlyphButtonControl`, `TouchTurnInteractControl`, `TouchControlSelectionRoute` …), строки
  `:touch_*`, `button.*`, `ctrl_*`, `#joystick_visibility_*`, `#static_joystick`, `#sneak_hold/toggle`.
* `assets/assets/resource_packs/vanilla/ui/hud_screen.json` — тача там нет (только HUD), поэтому геометрию
  брать из бинарника дизассемблером, а не из JSON.
* `textures/gui/touchgui.png`, `touchgui2.png` — атласы кнопок.

## 8. Готовый промпт для нового агента

> В репозитории `oneshot-horizon-builds` лежит `docs/agent-handoff/HANDOFF.md` и патч
> `android-patches/0028-android-bedrock-controls.patch` (управление как в Bedrock для Android-порта
> Rayan-XOO/horizon, пин ca93b0b). Прочитай HANDOFF.md и TOUCH-CONTROLS.md, наложи патч на дерево
> «порт + все патчи из android-patches/» (`git apply --check` сначала), прогони
> `cargo check -p horizon-client --lib` и почини ошибки компиляции, если они есть. Ничего в поведении
> не меняй без указания: цель — чтобы патч собирался.
