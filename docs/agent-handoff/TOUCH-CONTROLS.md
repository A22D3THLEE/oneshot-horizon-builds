# Патч 0028: управление как в Bedrock (Android)

Файл: `0028-android-bedrock-controls.patch` (один файл, `crates/horizon-client/src/game/touch.rs`, +407/−69).
Применяется после `0027`; проверено `git apply --check` на дереве «порт + все ваши патчи», в том числе на
LF-чекауте (как в Linux-CI).

## Что взято из кода Bedrock

В `libminecraftpe.so` (313 МБ, APK 1.26.40.5) сохранились RTTI-имена и строчные ключи, по ним и собран
набор. Ниже — то, что перенесено, и чем это стало в Horizon.

| Bedrock (`libminecraftpe.so`) | В патче |
| --- | --- |
| `button.fly_up_slow`, `button.fly_down_slow` | `Id::FlyUp` / `Id::FlyDown`: показываются только когда `player.flying` (`touch_flying()`), жмут `South` (вверх) и `RightStick` (вниз) — то же, чем игра летает с клавиатуры |
| `button.build_or_interact` (контекстное действие) | `Id::Action`: заменяет костыль `Mount` в Bedrock-пресете, жмёт триггер использования (0) как `use` |
| `#static_joystick`, `#joystick_visibility_*` | `stick_floating`: джойстик появляется под пальцем в левой половине; `stick_always` — рисовать его и без пальца |
| `:touch_sprint_double_tap` | двойной тап по джойстику (в пределах 300 мс) включает спринт |
| `sprint_on_movement` | `sprint_on_movement`: стик до упора вперёд → спринт (раньше было захардкожено на пресет) |
| `ctrl_islefthanded` | `left_handed`: зеркалит все контролы, кроме кнопки «…» у хотбара |
| `ctrl_top_button_scale` | `top_scale`: масштаб верхнего ряда (0.8/1.0/1.2/1.4, по кругу из редактора) |
| `ctrl_sensitivity2` | `look_scale`: множитель поворота камеры пальцем |
| `ctrl_dwellbeforedragtime` | `hold_ms`: сколько держать палец до начала добычи (было константой 280 мс) |
| `#sneak_hold` / `#sneak_toggle` | уже было (`toggle_sneak`/`toggle_crouch`) — не трогал |

Мёртвая зона джойстика добавлена по поведению Bedrock: пока стик в пределах 12 % — движения нет.

## Что появилось в интерфейсе

Раскладка Bedrock-пресета снята замером с самого Bedrock на планшете 3:2 (GUI ≈ 400×270):

* **Джойстик** фиксированный и всегда виден: квадрат на треть высоты экрана (`size` 44), центр на 55 % высоты.
* **Справа три кнопки** по ⅛ высоты (`size` 18): прыжок над приседом, спринт левее между ними.
  В полёте на их местах стоят **вверх/вниз** (`swapped_out()`), без полёта их нет.
* **Вверху по центру** три маленькие плитки (`size` 7): камера, чат, пауза.
* Кнопки действия, прицела и шестерёнки на HUD больше нет: тап — использовать/ударить, удержание — ломать.
  **Редактор** открывается кнопкой рядом с профилем на экране паузы (`edit_entry()`).
* В редакторе три дополнительные кнопки: **Left hand**, **Top size**, **Stick** (плавающий джойстик).

## Тонкая настройка без пересборки

Всё лежит в `touch_layout_v4.json` в папке игры (создаётся редактором):

```json
{
  "left_handed": false,
  "top_scale": 1.0,
  "stick_floating": false,
  "stick_always": false,
  "look_scale": 1.0,
  "hold_ms": 280,
  "sprint_on_movement": true
}
```

Новые умолчания лежат в новом файле (v4), старый `touch_layout_v3.json` не читается. Джойстик по умолчанию
фиксированный, как в Bedrock; плавающий включается кнопкой **Stick** в редакторе.

## Чего в патче нет (следующие шаги)

* `button.block_select` (выбор блока) — в Horizon нет аналога среднего клика в пэде, нужен отдельный вызов.
* `#touch_progress_bar_visible` — кольцо прогресса добычи под пальцем (нужен доступ к прогрессу ломания).
* `ctrl_stacksplittingtriggertime` (дележ стака долгим тапом), `ctrl_swapjumpandsneak`.
* Визуал: иконки/скругления как в `textures/gui/touchgui.png` (атлас Bedrock вытащен, 256×256).
* UI-слайдеры для `look_scale`/`hold_ms` — пока только JSON и редактор для трёх переключателей.

## Как проверить сборку

Важно: `touch.rs` **не** закрыт `#[cfg(target_os = "android")]` (`crates/horizon-client/src/game.rs:312`,
`mod touch;`), поэтому типы проверяются обычным хост-`cargo check`, без NDK:

```sh
cd <порт с наложенными патчами>
cargo check -p horizon-client --lib          # тайпчек, ~10 минут на холодную
cargo check -p horizon-android --target aarch64-linux-android   # полная проверка для Android
```

Полная сборка — как обычно: `src/packaging/android/build_apk.sh` или ваш `android.yml`.

Локально здесь скомпилировать не удалось, причины конкретные:

* `dl.google.com` отдаёт ~14 КБ/с (NDK r27c — 700 МБ), `static.crates.io` — ~115 КБ/с;
* в песочнице у cargo ломается TLS (`schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS`),
  поэтому докачать 93 отсутствующих в кэше крейта он не может (git с openssl-бэкендом работает, cargo — нет);
* в кэше `C:\Users\user\.cargo` не хватает 93 внешних крейтов из `Cargo.lock` этого пина (например
  `zip-9.4.1`, `jni-0.21.1`, `libmimalloc-sys-0.1.49`), подложить их неоткуда.

`rustfmt --emit stdout` файл разбирает без ошибок (синтаксис и скобки в порядке), но типы не проверены —
если CI ругнётся, пришлите вывод компилятора, поправлю.
