# vial-web-zh-cn

Web (WASM) build of the [Vial](https://github.com/vial-kb/vial-gui) configurator with the
Simplified-Chinese interface from [`Iemooon/vial-gui-zh-cn`](https://github.com/Iemooon/vial-gui-zh-cn)
(branch `zh-cn`).

Forked from `vial-kb/vial-web`. Upstream changes are merged into `main`; the localization wiring
lives on branch `zh-cn`.

## What is actually changed vs upstream

One line. The build job clones the localized GUI instead of the upstream one:

```sh
git clone -b zh-cn https://github.com/Iemooon/vial-gui-zh-cn.git vial-gui   # was: vial-kb/vial-gui
```

`src/build.sh` copies `vial-gui/src/main/python/*` into the preloaded filesystem, so the
`i18n/` package travels along with it, and `webmain.py` on the `zh-cn` branch installs the
translator before the window is built. Nothing else in the packaging layer needs to know
that a translation exists.

The `.github/workflows/main.yml` of upstream (auto-run on every push) is replaced by
`.github/workflows/zh-cn-web.yml`, which runs only on `workflow_dispatch`.

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

Nothing is fetched from the network at run time: the only URLs inside `index.html` and the loader
are documentation links shown in an error message. The whole app is those six files.

## Caveats worth checking first

* **Chinese glyph rendering has never been exercised by the upstream web build** (its UI is
  English-only). If the Chinese labels come out as boxes, the WASM Qt font database has no CJK
  face available; the fix is to put a CJK font into the preloaded filesystem and register it
  with `QFont.addApplicationFont()` from `i18n.install()`.
* The page shell itself (`Start Vial`, the unlock prompt, error messages) is plain HTML in
  `src/index.html` and is not covered by the Python translation layer.
