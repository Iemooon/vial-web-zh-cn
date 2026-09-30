# vial-web-zh-cn

Web (WASM) build of the [Vial](https://github.com/vial-kb/vial-gui) configurator with the
Simplified-Chinese interface from [`Iemooon/vial-gui-zh-cn`](https://github.com/Iemooon/vial-gui-zh-cn)
(branch `zh-cn`).

Forked from `vial-kb/vial-web`. Upstream changes are merged into `main`; the localization wiring
lives on branch `zh-cn`.

## What is actually changed vs upstream

Four things, all in the packaging layer plus one line of CI:

1. **`.github/workflows/zh-cn-web.yml`** replaces upstream's `main.yml` (which ran on every
   push).  It runs only on `workflow_dispatch` and clones the localized GUI:

   ```sh
   git clone -b zh-cn https://github.com/Iemooon/vial-gui-zh-cn.git vial-gui   # was: vial-kb/vial-gui
   ```

   `src/build.sh` copies `vial-gui/src/main/python/*` into the preloaded filesystem, so the
   `i18n/` package travels with it and `webmain.py` on the `zh-cn` branch installs the
   translator before the window is built.
2. **`fonts/NotoSansSC-Regular.otf`** (see `fonts/README.md`) and two lines in `src/build.sh`
   that put it into `usr/local/fonts/`.  Qt in the browser cannot see system fonts, so the
   Chinese text would come out as boxes without it; `i18n.ensure_cjk_font()` registers it at
   startup and leaves desktop builds untouched.
3. **`src/index.html`** passes a `?theme=` URL parameter into `webmain.main()`.
4. **`-sTOTAL_MEMORY`** raised from 20 MB to 64 MB, because the preloaded filesystem now
   carries a font as well.

## Theme

Upstream hides the Theme menu in the web build (`main_window.py`: `if sys.platform !=
"emscripten"`), but the palettes in `themes.py` are pure Python and work fine under WASM, so
`webmain.py` puts the menu back: 主题 → 跟随系统 / 浅色 / 深色.

The menu changes the palette for the current session.  A choice does **not** survive a reload
(the WASM filesystem is recreated every time, so `QSettings` cannot persist), which is what the
URL parameter is for:

```
http://localhost:8000/?theme=light
```

`theme=light`, `theme=dark`, `theme=system` (case-insensitive).  Bookmark the URL to keep the choice.

### Two keyboards on one desk

Upstream's `connect()` accepts **exactly one** device: `if (devices.length != 1) { go back }`.
With two Vial receivers plugged in -- or two still granted from an earlier session -- the button
simply returns to "Start Vial" and looks like the page cannot see the keyboard.  This fork reports
what it found instead, and `?pick=N` chooses one of them:

```
http://localhost:8000/?pick=0&theme=light
```

The device list is numbered in the message the button shows, and `chrome://settings/content/hid`
is where stale grants get removed.



## Build

Needs Linux + bash; it cross-compiles CPython and Qt5 with Emscripten, so expect a long run.

```sh
git clone -b zh-cn https://github.com/Iemooon/vial-gui-zh-cn.git vial-gui
git clone https://github.com/vial-kb/via-keymap-precompiled.git
./fetch-emsdk.sh && ./fetch-deps.sh && ./build-deps.sh
cd src && ./build.sh
```

Output is `src/build/`, six files, about 33 MB (verified on run 36539630046):

| file | size | what it is |
|---|---|---|
| `index.html` | 9 KB | the page shell; boots the module and does the WebHID handshake |
| `main-<UNIQVER>.js` | 347 KB | Emscripten loader |
| `main-<UNIQVER>.wasm` | 23.4 MB | CPython + Qt5 + PyQt5 + this app's C glue |
| `main-<UNIQVER>.data` | 9.3 MB | preloaded filesystem: all of `vial-gui/src/main/python`, the `i18n/` package included, plus `qmk_settings.json` / `build_settings.json` |
| `main-<UNIQVER>.worker.js` | 3.8 KB | pthread worker + the `vialglue` ↔ WebHID bridge |
| `icon.png` | 24 KB | favicon |

`<UNIQVER>` is the sha256 of the three commit ids, so the names change whenever any input
changes -- that is the cache-busting scheme, and it means all files must be deployed together.

## Deploy

The output is a plain static site, no server side involved, but two things are mandatory:

1. **`SharedArrayBuffer` requires a cross-origin-isolated page.** The CI writes a `_headers`
   file into the artifact for GitHub Pages. On any other host send these two headers yourself:

   ```
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Embedder-Policy: require-corp
   ```

2. **HTTPS or localhost.** The configurator talks to the keyboard over WebHID, which browsers
   only expose in a secure context. `http://127.0.0.1` is fine for local testing.

Browser support: Chrome / Chromium / Edge. Firefox and Safari have no WebHID, and the page
detects that and says so.

Local test run -- `python -m http.server` is **not** enough, it cannot send the two headers:

```sh
python tools/serve.py src/build 8000      # then open http://localhost:8000/  in Chrome/Edge
```

For GitHub Pages: enable Pages for the repository and point it at the `gh-pages` branch, or run
the workflow with the `deploy` checkbox ticked, which force-pushes the build there.

### Checking a build without plugging a keyboard in

`tools/render-harness.py <artifact-dir> [theme]` writes `render-test.html` next to the artifact:
same runtime, but the WebHID step is replaced by "no devices found", so the real window comes up
and can be screenshotted.  Any Python error is painted into a message box instead of vanishing
into a console nobody reads.  This is how the Qt5 `QActionGroup` import bug (which blanked the
whole app) was found.

```sh
python tools/render-harness.py src/build Light
python tools/serve.py src/build 8000
# open http://localhost:8000/render-test.html
```


Nothing is fetched from the network at run time: the only URLs inside `index.html` and the loader
are documentation links shown in an error message. The whole app is those six files.

## Caveats

* **Chinese glyph rendering** needed a bundled font, which is what `fonts/` is for.  It is
  registered by `i18n.ensure_cjk_font()`; if the labels ever come out as boxes again, check
  that `usr/local/fonts/NotoSansSC-Regular.otf` is inside the `.data` file (the CI prints this).
* The page shell itself (`Start Vial`, the unlock prompt, error messages) is plain HTML in
  `src/index.html` and is not covered by the Python translation layer.
* Upstream's own workaround for the missing font is still active: non-ASCII **key labels** in
  the keycode tray are replaced by their `KC_...` names under Emscripten
  (`keycodes.py`).  That is upstream behaviour, not something this fork changes.

