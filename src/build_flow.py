"""Собирает единый прототип: поиск → каталог → карточка → бронирование → бронь.
CSS каждого экрана изолируется префиксом, чтобы классы не конфликтовали."""
import base64, pathlib, re, json

root = pathlib.Path(__file__).parent
ns = {"__file__": str(root / "build.py")}
exec((root / "build.py").read_text().split("html = (root")[0], ns)
SVG, a = ns["SVG"], root / "assets"
b64 = lambda p: base64.b64encode(p.read_bytes()).decode()


def split_rules(css):
    """Верхний уровень CSS: список (prelude, body) с учётом вложенных скобок."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        out.append((css[i:j].strip(), css[j + 1:k - 1]))
        i = k
    return out


def split_sel(sel):
    parts, depth, cur = [], 0, ""
    for ch in sel:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and not depth:
            parts.append(cur); cur = ""
        else:
            cur += ch
    return [p.strip() for p in parts + [cur] if p.strip()]


def scope(css, pfx):
    res = []
    for pre, body in split_rules(css):
        if pre.startswith("@font-face"):
            continue
        if pre.startswith("@keyframes"):
            name = pre.split()[1]
            res.append(f"@keyframes {pfx[1:]}-{name} {{{body}}}")
            continue
        if pre.startswith("@media") or pre.startswith("@supports"):
            res.append(f"{pre} {{{scope(body, pfx)}}}")
            continue
        sels = []
        for s in split_sel(pre):
            if s in (":root", "html", "body", "html, body"):
                sels.append(pfx)
            elif s.startswith(":root"):
                sels.append(pfx + s[5:])
            elif s == "*":
                sels += [pfx, f"{pfx} *"]
            elif s.startswith("*,") or s.startswith("*::"):
                sels.append(f"{pfx} {s}")
            else:
                sels.append(f"{pfx} {s}")
        res.append(f"{', '.join(dict.fromkeys(sels))} {{{body}}}")
    out = "\n".join(res)
    # анимации переименованы, чтобы экраны не перебивали друг друга
    for kf in re.findall(r"@keyframes\s+([\w-]+)", css):
        out = re.sub(rf"(animation(?:-name)?\s*:[^;}}]*?)\b{kf}\b", rf"\g<1>{pfx[1:]}-{kf}", out)
    return out


def between(s, a_, b_):
    i = s.index(a_) + len(a_)
    return s[i:s.index(b_, i)]


# 1. Поиск
t = (root / "template.html").read_text()
s_css = scope(between(t, "<style>", "</style>"), "#v-search")
s_body = between(t, "<body>", "</body>")
rep = [
    ('id="toast"', 'id="toast-s"'), ("$('#toast')", "$('#toast-s')"),
    ("const today = startOfDay(new Date());", "const today = new Date(2026, 9, 10);"),
    ("    const msg = `Ищем авто: ${parts.join(' · ')}`;\n    status.textContent = msg; showToast(msg);",
     "    status.textContent = 'Ищем машины';\n    const btn = $('.search__submit'); btn.classList.add('is-loading');\n    setTimeout(() => { WK.go('catalog'); btn.classList.remove('is-loading'); }, 650);"),
    ('<a class="logo" href="#"', '<a class="logo" href="#" onclick="event.preventDefault()"'),
]
for x, y in rep:
    assert s_body.count(x) == 1, x
    s_body = s_body.replace(x, y)
s_css += "\n#v-search .search__submit.is-loading { opacity: .7; pointer-events: none; } #v-search .search__submit.is-loading svg { animation: wk-pulse .8s ease-in-out infinite alternate; }"

# 2. Каталог и карточка
p = (root / "pages.html").read_text()
p_css = scope(between(p, "<style>", "</style>"), ".vp")
p_body = p[p.index("</style>") + 8:]

# 3. Бронирование
bk = (root / "booking.html").read_text()
b_css = scope(between(bk, "<style>", "</style>"), "#v-book")
b_body = bk[bk.index("</style>") + 8:]

shell_css = """
@font-face { font-family: "PT Root UI VF"; src: url(data:font/woff2;base64,{{FONT}}) format("woff2"); font-weight: 300 700; font-display: swap; }
@font-face { font-family: "Onest"; src: url(data:font/woff2;base64,{{ONEST_CYR}}) format("woff2"); font-weight: 600; font-display: swap; unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116; }
@font-face { font-family: "Onest"; src: url(data:font/woff2;base64,{{ONEST_LAT}}) format("woff2"); font-weight: 600; font-display: swap; unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }
:root {
  color-scheme: light;
  --white: #ffffff; --c50: #f5f4f2; --c100: #e8e7e5; --c200: #dcdbd7; --c300: #c8c6c2; --c400: #a8a6a1;
  --c500: #83827d; --c600: #62605b; --c800: #3a3936; --c900: #262623;
  --sage-50: #edf2ed; --sage-100: #dfe7e0; --sage-300: #b7c7b9; --sage-500: #738776; --sage-600: #526456;
  --on-dark: #f6f4f2;
  --font-ui: "PT Root UI VF", "PT Root UI", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-display: "Onest", "PT Root UI VF", system-ui, sans-serif;
  --ease: cubic-bezier(.22,.8,.24,1);
}
html, body { margin: 0; }
body { background: var(--c50); color: var(--c900); font-family: var(--font-ui); font-size: 17px; line-height: 26px; -webkit-font-smoothing: antialiased; }
[hidden] { display: none !important; }
.screen { min-height: 100vh; background: var(--c50); }
.vp { font-family: var(--font-ui); }
::view-transition-old(root) { animation: .4s cubic-bezier(.4,0,.6,1) both wk-out; }
::view-transition-new(root) { animation: .7s cubic-bezier(.22,.8,.24,1) .12s both wk-in; }
.screen.wk-enter { animation: wk-in .7s cubic-bezier(.22,.8,.24,1) both; }
@keyframes wk-out { to { opacity: 0; } }
@keyframes wk-in { from { opacity: 0; transform: translateY(10px); } }
@keyframes wk-pulse { to { transform: scale(1.18); } }
@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }
"""

shell_js = """
<script>
window.WK = (() => {
  const views = { search: "v-search", catalog: "v-cat", card: "v-card", booking: "v-book" };
  let cur = "search";
  const W = { extras: { seat: false, delivery: false }, onEnter: {}, onAuth: [], cur: () => cur };
  W.total = () => 35280 + (W.extras.delivery ? 500 : 0);
  W.auth = name => W.onAuth.forEach(f => f(name));
  W.go = name => {
    if (name === cur) return;
    const from = cur, a = document.getElementById(views[from]), b = document.getElementById(views[name]);
    const swap = () => {
      a.hidden = true; b.hidden = false; cur = name; window.scrollTo(0, 0);
      if (name === "booking" && W.book) W.book.enter();
      (W.onEnter[name] || (() => {}))(from);
    };
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (document.startViewTransition && !reduce) { document.startViewTransition(swap); return; }
    swap(); if (!reduce) { b.classList.remove("wk-enter"); b.offsetWidth; b.classList.add("wk-enter"); }
  };
  return W;
})();
</script>
"""

html = (
    '<title>WayKit: аренда авто</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
    f"<style>{shell_css}\n{s_css}\n{p_css}\n{b_css}</style>\n{shell_js}\n"
    f'<section class="screen" id="v-search" aria-label="Поиск">{s_body}</section>\n'
    f"{p_body}\n"
    f'<section class="screen" id="v-book" hidden aria-label="Бронирование">{b_body}</section>\n'
)

cars = [b64(a / "flow" / f"car{i}.jpg") for i in range(12)]
bkA = a / "booking"
R = {
    "FONT": b64(a / "pt-root-ui-vf.woff2"), "ONEST_CYR": b64(a / "onest-cyrillic-600-normal.woff2"),
    "ONEST_LAT": b64(a / "onest-latin-600-normal.woff2"), "HERO": b64(a / "hero.webp"),
    "CARS": json.dumps(cars), "MAIN": b64(a / "flow" / "main.jpg"),
    "THUMB0": b64(a / "flow" / "thumb0.jpg"), "THUMB1": b64(a / "flow" / "thumb1.jpg"), "THUMB2": b64(a / "flow" / "thumb2.jpg"),
    "CAR": b64(bkA / "car.jpg"), "DOC_MAIN": b64(bkA / "passport_main.jpg"), "DOC_REG": b64(bkA / "passport_reg.jpg"),
    "DOC_FRONT": b64(bkA / "license_front.jpg"), "DOC_BACK": b64(bkA / "license_back.jpg"),
}
R.update({"SVG_" + k: v for k, v in SVG.items()})
for k, v in R.items():
    html = html.replace("{{%s}}" % k, v)
assert "{{" not in html, [l[:120] for l in html.splitlines() if "{{" in l][:3]
out = root.parent / "dist" / "waykit-flow.html"
out.write_text(html)
print(out, len(html) // 1024, "KB")
