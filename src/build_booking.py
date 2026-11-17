import base64, pathlib
root = pathlib.Path(__file__).parent
src = (root / "build.py").read_text().split("html = (root")[0]
ns = {"__file__": str(root / "build.py")}
exec(src, ns)
a, SVG = root / "assets", ns["SVG"]
b64 = lambda p: base64.b64encode(p.read_bytes()).decode()
bk = a / "booking"
html = (root / "booking.html").read_text()
rep = {
    "FONT": b64(a / "pt-root-ui-vf.woff2"),
    "ONEST_CYR": b64(a / "onest-cyrillic-600-normal.woff2"),
    "ONEST_LAT": b64(a / "onest-latin-600-normal.woff2"),
    "CAR": b64(bk / "car.jpg"),
    "DOC_MAIN": b64(bk / "passport_main.jpg"),
    "DOC_REG": b64(bk / "passport_reg.jpg"),
    "DOC_FRONT": b64(bk / "license_front.jpg"),
    "DOC_BACK": b64(bk / "license_back.jpg"),
    "SVG_LOGO": SVG["LOGO"], "SVG_LOCATION": SVG["LOCATION"],
}
for k, v in rep.items():
    html = html.replace("{{%s}}" % k, v)
assert "{{" not in html, [l for l in html.splitlines() if "{{" in l][:3]
out = root.parent / "dist" / "waykit-booking.html"
out.write_text(html)
print(out, len(html) // 1024, "KB")
