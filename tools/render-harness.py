"""Make a page that boots the real Vial window with no keyboard attached.

Why: the shipped `index.html` only runs `webmain.main()` after WebHID hands it a
device, so a build cannot be checked without someone plugging a keyboard in and
clicking through the browser's device picker.  This writes `render-test.html`
next to `index.html`, which keeps the entire runtime identical and only replaces
the device step:

* `_vialglue_set_device_desc()` **must** be called.  Without it
  `vialglue.get_device_desc()` runs `PyUnicode_FromString(NULL)` and the worker
  dies outright -- the canvas stays blank and nothing is reported anywhere.
* `hid.enumerate` is stubbed to "no devices", which is the normal desktop state
  with nothing plugged in, so the window comes up and says so.
* Any exception is painted into a `QMessageBox`, because there is no console
  readable from here.  This is what caught the Qt5 `QActionGroup` import bug.

    python tools/render-harness.py <artifact-dir> [theme]
    python tools/serve.py <artifact-dir> 8000
    # then open http://localhost:8000/render-test.html  in Chrome/Edge

Expect: menu bar 文件 / 键盘布局 / 关于 / 主题 (more menus appear once a keyboard
is actually connected), the "未检测到设备" notice, and -- since the bundled
Noto Sans SC -- correct Chinese glyphs.  With a theme argument the palette is
applied by `webmain.main()`, so a light background means `?theme=` works end to
end.
"""
import json
import os
import sys

art = sys.argv[1] if len(sys.argv) > 1 else "src/build"
theme = sys.argv[2] if len(sys.argv) > 2 else "Light"

index = os.path.join(art, "index.html")
if not os.path.isfile(index):
    sys.exit("no index.html in %s (download the artifact first)" % art)
html = open(index, encoding="utf-8").read()

PYSRC = """
import traceback
try:
    import hidproxy
    hidproxy.hid.enumerate = staticmethod(lambda: [])
    import webmain
    webmain.main(qtApp, %r)
except Exception:
    from PyQt5.QtWidgets import QMessageBox
    _box = QMessageBox()
    _box.setWindowTitle("harness error")
    _box.setText(traceback.format_exc()[-1500:])
    _box.show()
    qtApp.processEvents()
""" % theme

BOOT = """
    // ---- tools/render-harness.py: boot the real window without a device ----
    function test_boot() {
        g_device = {sendReport: function() {}};
        var device_desc = {
            path: "/webhid", vendor_id: 0x1313, product_id: 0x1208,
            serial_number: "", release_number: 1, manufacturer_string: "",
            product_string: "HARNESS (no device)", usage_page: 65376,
            usage: 97, interface_number: 1
        };
        _vialglue_set_device_desc(allocateUTF8(JSON.stringify(device_desc)));
        document.getElementById("startup").style.display = "none";
        PThread.runningWorkers[0].postMessage({cmd: "py", payload: %s});
    }
    async function connect() {""" % json.dumps(PYSRC)

anchor = "    async function connect() {"
if html.count(anchor) != 1:
    sys.exit("expected exactly one `async function connect() {` in index.html")
html = html.replace(anchor, BOOT.lstrip("\n").rstrip() + "\n")

flag = 'document.getElementById("startup_btn").disabled = false;'
if flag not in html:
    sys.exit("notify_alive hook not found in index.html -- upstream changed?")
html = html.replace(flag, flag + " test_boot();", 1)

out = os.path.join(art, "render-test.html")
open(out, "w", encoding="utf-8", newline="\n").write(html)
print("wrote %s (theme=%s)" % (out, theme))
