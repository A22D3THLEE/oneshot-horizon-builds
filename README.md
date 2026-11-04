# Oneshot builds of Horizon

[Horizon](https://github.com/horizon-rust/horizon) (Minecraft Java 26.3 rewritten in Rust) built for Windows with
the small changes Oneshot Launcher needs, for every new Horizon release, by GitHub Actions.

| Patch | What it does |
| --- | --- |
| `patches/0001-skin-share.patch` | Skins in offline-mode multiplayer (LAN, play with friends): the host asks each joining player for their Mojang-signed skin (login plugin channel `oneshot:skin`) and shows it to everyone, as an online-mode server would. Every client still checks Mojang's signature. A client without the patch answers "unknown channel" and joins as before. |

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
