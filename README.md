# Oneshot builds of Horizon

Канал авторов / Authors' channel: **[t.me/oneshot_tg](https://t.me/oneshot_tg)**

## Download the launcher

**[OneshotLauncher.exe](https://github.com/A22D3THLEE/oneshot-horizon-builds/releases/latest)**: pick the newest release named `launcher-v...` (Oneshot Launcher), download `OneshotLauncher.exe` and run it. The launcher updates itself and installs Horizon and its Oneshot builds. Windows may show a SmartScreen warning: the file is not signed yet.

[Horizon](https://github.com/horizon-rust/horizon) (Minecraft Java 26.3 rewritten in Rust) built for Windows with
the small changes Oneshot Launcher needs, for every new Horizon release, by GitHub Actions.

| Patch | What it does |
| --- | --- |
| `patches/0001-skin-share.patch` | Skins in offline-mode multiplayer (LAN, play with friends): the host asks each joining player for their Mojang-signed skin (login plugin channel `oneshot:skin`) and shows it to everyone, as an online-mode server would. Every client still checks Mojang's signature. A client without the patch answers "unknown channel" and joins as before. |
| `patches/0002-vertex-packing.patch` | Terrain vertices take 20 bytes instead of 24 (a power-of-two position step per vertex, decoded with `ldexp` in `terrain.wgsl`): 17% less vertex memory, 170-270 MB less RAM at render distance 32 on an RX 5700 XT, the same picture (render tests and screenshots against the official build). Only the client draws differently; multiplayer is unaffected. |

## How a build is made

`.github/workflows/build.yml`, every 4 hours and by hand:

1. finds the newest Horizon nightly and stable release with a Windows build that isn't built here yet;
2. downloads the official `horizon-windows-x64.zip` and takes the SHA-256 of its `horizon-client.exe`;
3. checks out Horizon's source at the release's commit and applies `patches/*.patch`;
4. builds `horizon-client` as Horizon's own release workflow does (MSVC, `+crt-static`, `HORIZON_VERSION`,
   `HORIZON_NIGHTLY`);
5. publishes the release `oneshot-<first 16 hex of the official SHA-256>` with `horizon-client-oneshot.zip` and
   `build.txt` (`base`, `sha256`, `features`, `horizon`).

Oneshot Launcher computes the SHA-256 of an installed version's official `horizon-client.exe`, downloads the
release with that name, checks `build.txt` and the program's SHA-256, and plays it next to the official game
(`horizon-client-oneshot.exe`). A version without a build here runs the official game.

When a Horizon release changes the code a patch touches, `git apply` fails and that release gets no build until
the patch is updated.

Horizon is © its authors under its own license; see the upstream repository.
