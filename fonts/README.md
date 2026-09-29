# fonts/

`NotoSansSC-Regular.otf` — 8,331,336 bytes, sha256
`faa6c9df652116dde789d351359f3d7e5d2285a2b2a1f04a2d7244df706d5ea9`, `OTTO` (CFF) flavour.

Taken from the official Noto CJK repository:
<https://github.com/notofonts/noto-cjk/blob/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf>
(the Simplified-Chinese subset of Noto Sans SC).  Noto is licensed under the
SIL Open Font License 1.1, which permits redistribution in unmodified form; the
license text is published with the project at
<https://openfontlicense.org/>.  That repository carries no `LICENSE` file at its
root, so the pointer above is the authoritative source rather than a copy.

## Why the font is vendored here instead of downloaded by CI

Qt compiled to WebAssembly has no access to operating-system fonts — it lays out
and rasterises text itself through FreeType, over whatever font files it is given.
Upstream vial-gui works around that by replacing non-ASCII key labels with ASCII
text (`src/main/python/keycodes/keycodes.py`: "we cannot embed full CJK fonts due
to large size"), which a Chinese interface cannot do.  So the packaging layer puts
this file into the preloaded filesystem (`src/build.sh` → `usr/local/fonts/`) and
`i18n.ensure_cjk_font()` registers it at startup.

Vendoring rather than a CI download keeps the build reproducible and offline-safe,
and the file name is stable, so the usual `.data` cache-busting (the `UNIQVER` in
the file names) still covers it.

Cost: `.data` grows from 9.3 MB to about 17.6 MB, first load about 41 MB in total.
A subsetted font would be smaller but would turn any character outside the subset
— a keyboard's own name, a layout name, an error message quoting a file name —
into blanks, so the full Simplified-Chinese subset is kept.
