#!/usr/bin/env python3
"""HMİ — özgün mimari konsept çizimleri (SVG) üreteci.
Aksonometri + cephe/kesit çizimleri; açık (kağıt) ve koyu (gece paftası) temalar."""
import math, os

OUT = "img/illus"
os.makedirs(OUT, exist_ok=True)
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))

THEMES = {
    "light": dict(bg="#f4f1ea", paper="#efe9db", ink="#15120c", ink2="#534c3f", gold="#a8772a", gold2="#c89436",
                  wallF="#ece6d8", wallS="#ddd5c3", roof="#d3c9b0", roof2="#c4b89c", glass="#c6d1cf", glass2="#adbcbb",
                  stone="#e4dccb", brick="#b97a62", ground="#eae3d2", green="#9fae86", green2="#7f9169", water="#8fb1b8",
                  door="#bfb6a2", text="#15120c"),
    "dark":  dict(bg="#161310", paper="#1d1915", ink="#f6f2ea", ink2="#bfb7a8", gold="#c89436", gold2="#e0b358",
                  wallF="#2b2620", wallS="#221e19", roof="#332d25", roof2="#2a251e", glass="#354547", glass2="#2a383a",
                  stone="#2f2a23", brick="#6e4636", ground="#1f1b16", green="#33402c", green2="#28321f", water="#2f4a52",
                  door="#3a342b", text="#f6f2ea"),
}

class Canvas:
    def __init__(self, w, h, theme, scale, ox, oy, anim=False):
        self.w, self.h, self.t, self.s, self.ox, self.oy = w, h, THEMES[theme], scale, ox, oy
        self.el = []
        self.anim = anim
    def iso(self, x, y, z):
        return (self.ox + (x - y) * C30 * self.s, self.oy + (x + y) * S30 * self.s - z * self.s)
    def pts(self, P):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in P)
    def poly(self, P, fill, stroke=None, sw=1.3, op=1, dash=None):
        stroke = stroke or self.t["ink"]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<polygon points="{self.pts(P)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" opacity="{op}"{d} pathLength="1"/>')
    def line(self, a, b, stroke=None, sw=1, dash=None, op=1):
        stroke = stroke or self.t["ink"]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" opacity="{op}"{d} pathLength="1"/>')
    def text(self, x, y, s, size=13, fill=None, anchor="start", weight=400, family="serif", ls=0, italic=False):
        fill = fill or self.t["text"]
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        fam = "Georgia, 'Times New Roman', serif" if family == "serif" else "Helvetica, Arial, sans-serif"
        st = " font-style=\"italic\"" if italic else ""
        self.el.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}"{st}>{s}</text>')
    def circle(self, x, y, r, fill, stroke=None, sw=1):
        stroke = stroke or self.t["ink"]
        self.el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" pathLength="1"/>')
    def ellipse(self, x, y, rx, ry, fill, stroke=None, sw=1):
        stroke = stroke or self.t["ink"]
        self.el.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" pathLength="1"/>')
    def rect(self, x, y, w, h, fill, stroke=None, sw=1.2, rx=0):
        stroke = stroke or self.t["ink"]
        self.el.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" pathLength="1"/>')

    # ---------- iso primitives ----------
    def ground(self, x0, y0, x1, y1, fill=None, hatch=True):
        t = self.t
        P = [self.iso(x0, y0, 0), self.iso(x1, y0, 0), self.iso(x1, y1, 0), self.iso(x0, y1, 0)]
        self.poly(P, fill or t["ground"], t["ink2"], 1, 1)
        if hatch:
            for k in range(0, int(x1 - x0) + 1, 4):
                self.line(self.iso(x0 + k, y0, 0), self.iso(x0 + k, y1, 0), t["ink2"], .35, op=.5)
            for k in range(0, int(y1 - y0) + 1, 4):
                self.line(self.iso(x0, y0 + k, 0), self.iso(x1, y0 + k, 0), t["ink2"], .35, op=.5)
    def box(self, x0, y0, w, d, z0, h, top=True, fillF=None, fillS=None, fillT=None):
        t = self.t; x1, y1 = x0 + w, y0 + d
        if top:
            self.poly([self.iso(x0, y0, z0 + h), self.iso(x1, y0, z0 + h), self.iso(x1, y1, z0 + h), self.iso(x0, y1, z0 + h)], fillT or t["roof"])
        self.poly([self.iso(x1, y0, z0), self.iso(x1, y1, z0), self.iso(x1, y1, z0 + h), self.iso(x1, y0, z0 + h)], fillS or t["wallS"])
        self.poly([self.iso(x0, y1, z0), self.iso(x1, y1, z0), self.iso(x1, y1, z0 + h), self.iso(x0, y1, z0 + h)], fillF or t["wallF"])
    def gable(self, x0, y0, w, d, z0, he, hr, ridge="x", fillF=None, fillS=None):
        """box + gable roof. ridge along x (default) or y."""
        t = self.t; x1, y1 = x0 + w, y0 + d
        self.box(x0, y0, w, d, z0, he, top=False, fillF=fillF, fillS=fillS)
        if ridge == "x":
            ym = y0 + d / 2
            # end gable triangle on x1 face
            self.poly([self.iso(x1, y0, z0 + he), self.iso(x1, ym, z0 + hr), self.iso(x1, y1, z0 + he)], fillS or t["wallS"])
            # front slope (y from ym to y1)
            self.poly([self.iso(x0, ym, z0 + hr), self.iso(x1, ym, z0 + hr), self.iso(x1, y1, z0 + he), self.iso(x0, y1, z0 + he)], t["roof"])
            # back slope (partially visible from above): draw for completeness
            self.poly([self.iso(x0, y0, z0 + he), self.iso(x1, y0, z0 + he), self.iso(x1, ym, z0 + hr), self.iso(x0, ym, z0 + hr)], t["roof2"])
        else:
            xm = x0 + w / 2
            self.poly([self.iso(x0, y1, z0 + he), self.iso(xm, y1, z0 + hr), self.iso(x1, y1, z0 + he)], fillF or t["wallF"])
            self.poly([self.iso(xm, y0, z0 + hr), self.iso(xm, y1, z0 + hr), self.iso(x1, y1, z0 + he), self.iso(x1, y0, z0 + he)], t["roof"])
            self.poly([self.iso(x0, y0, z0 + he), self.iso(xm, y0, z0 + hr), self.iso(xm, y1, z0 + hr), self.iso(x0, y1, z0 + he)], t["roof2"])
    def winF(self, y1, u0, u1, z0, z1, fill=None, grid=0):
        """window on max-y (front) face at plane y=y1 spanning x u0..u1"""
        t = self.t
        self.poly([self.iso(u0, y1, z0), self.iso(u1, y1, z0), self.iso(u1, y1, z1), self.iso(u0, y1, z1)], fill or t["glass"], t["ink"], .9)
        if grid:
            n = max(1, int((u1 - u0) / grid))
            for i in range(1, n):
                u = u0 + (u1 - u0) * i / n
                self.line(self.iso(u, y1, z0), self.iso(u, y1, z1), t["ink2"], .5, op=.7)
            m = max(1, int((z1 - z0) / grid))
            for i in range(1, m):
                z = z0 + (z1 - z0) * i / m
                self.line(self.iso(u0, y1, z), self.iso(u1, y1, z), t["ink2"], .5, op=.7)
    def winS(self, x1, v0, v1, z0, z1, fill=None, grid=0):
        t = self.t
        self.poly([self.iso(x1, v0, z0), self.iso(x1, v1, z0), self.iso(x1, v1, z1), self.iso(x1, v0, z1)], fill or t["glass"], t["ink"], .9)
        if grid:
            n = max(1, int((v1 - v0) / grid))
            for i in range(1, n):
                v = v0 + (v1 - v0) * i / n
                self.line(self.iso(x1, v, z0), self.iso(x1, v, z1), t["ink2"], .5, op=.7)
            m = max(1, int((z1 - z0) / grid))
            for i in range(1, m):
                z = z0 + (z1 - z0) * i / m
                self.line(self.iso(x1, v0, z), self.iso(x1, v1, z), t["ink2"], .5, op=.7)
    def tree(self, x, y, r=2.2, h=3.5):
        t = self.t
        bx, by = self.iso(x, y, 0)
        tx, ty = self.iso(x, y, h)
        self.line((bx, by), (tx, ty), t["ink2"], 1.2)
        self.ellipse(tx, ty - r * self.s * .5, r * self.s * .9, r * self.s * .75, t["green"], t["ink2"], .9)
        self.ellipse(tx - r * self.s * .3, ty - r * self.s * .7, r * self.s * .55, r * self.s * .45, t["green2"], t["ink2"], .7)
    def hedge(self, x0, y0, x1, y1, w=1.4, h=1.6):
        t = self.t
        # oriented along x or y
        if abs(x1 - x0) > abs(y1 - y0):
            self.box(min(x0, x1), y0 - w / 2, abs(x1 - x0), w, 0, h, fillF=t["green"], fillS=t["green2"], fillT=t["green"])
        else:
            self.box(x0 - w / 2, min(y0, y1), w, abs(y1 - y0), 0, h, fillF=t["green"], fillS=t["green2"], fillT=t["green"])
    def label_iso(self, x, y, z, s, size=12, dy=-6):
        px, py = self.iso(x, y, z)
        self.text(px, py + dy, s, size, self.t["gold"], "middle", 600, "sans", 1.5)
    def tag(self, x, y, z, num):
        px, py = self.iso(x, y, z)
        self.circle(px, py, 13, self.t["bg"], self.t["ink"], 1.4)
        self.text(px, py + 5, str(num), 14, self.t["ink"], "middle", 700, "sans")

    # ---------- title block ----------
    def title(self, project, drawing, note="Konsept çizim · Ölçeksiz", x=None, y=None, w=470):
        t = self.t
        x = self.w - w - 34 if x is None else x
        y = self.h - 118 if y is None else y
        self.rect(x, y, w, 86, t["paper"], t["gold"], 1.2)
        self.line((x + 74, y), (x + 74, y + 86), t["gold"], 1)
        self.text(x + 37, y + 55, "HMİ", 30, t["gold"], "middle", 700, "serif")
        self.text(x + 92, y + 30, project, 19, t["text"], "start", 400, "serif")
        self.text(x + 92, y + 53, drawing.upper(), 10.5, t["gold"], "start", 600, "sans", 2.4)
        self.text(x + 92, y + 73, note + " · Haşimoğlu Mimarlık İnşaat · 2026", 10, t["ink2"], "start", 400, "sans", .4)
    def north(self, x, y):
        t = self.t
        self.circle(x, y, 18, "none", t["ink2"], 1)
        self.poly([(x, y - 16), (x - 6, y + 4), (x, y), (x + 6, y + 4)], t["gold"], t["ink"], 1)
        self.text(x, y - 24, "K", 11, t["ink2"], "middle", 600, "sans")
    def scalebar(self, x, y, meters, label):
        t = self.t
        L = meters * self.s * C30 * 2 / 2  # approximate iso x length
        self.line((x, y), (x + L, y), t["ink2"], 1.4)
        for k in range(0, 3):
            self.line((x + L * k / 2, y - 4), (x + L * k / 2, y + 4), t["ink2"], 1.2)
        self.text(x, y + 16, "0", 10, t["ink2"], "start", 400, "sans")
        self.text(x + L, y + 16, label, 10, t["ink2"], "end", 400, "sans")

    def render(self, path, title_text):
        t = self.t
        anim_css = ""
        if self.anim:
            anim_css = """<style>
  polygon,line,circle,ellipse,rect{stroke-dasharray:1;stroke-dashoffset:1;animation:hmi-draw 4.6s cubic-bezier(.4,0,.2,1) forwards,hmi-fill 3s ease 3.2s forwards;fill-opacity:0}
  text{opacity:0;animation:hmi-txt 1.2s ease 5.2s forwards}
  @keyframes hmi-draw{to{stroke-dashoffset:0}}
  @keyframes hmi-fill{to{fill-opacity:1}}
  @keyframes hmi-txt{to{opacity:1}}
</style>"""
        body = "\n".join(self.el)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{title_text}">
<title>{title_text}</title>{anim_css}
<rect width="{self.w}" height="{self.h}" fill="{t["bg"]}"/>
{body}
</svg>'''
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  {path}  ({len(svg)//1024} KB)")

# ---------------------------------------------------------------- 1) DEKOR SAFARI — aksonometri
def dekor_safari_axo(theme, path, anim=False, hero=False):
    c = Canvas(1600, 900, theme, 9.2 if not hero else 10.4, 790, 250 if not hero else 230, anim)
    t = c.t
    c.ground(-6, -6, 84, 50)
    # road
    c.poly([c.iso(-6, 44, 0), c.iso(84, 44, 0), c.iso(84, 50, 0), c.iso(-6, 50, 0)], t["door"], t["ink2"], .8)
    # hedge line on north
    c.hedge(0, -2, 78, -2)
    # main production hall  66 x 34, eave 8, ridge 10.5   (≈2.244 m²)
    c.gable(6, 4, 66, 34, 0, 8, 10.6, "x")
    # clerestory/roof lights on front slope
    for i in range(6):
        u0 = 12 + i * 10
        c.poly([c.iso(u0, 22.5, 9.9), c.iso(u0 + 6, 22.5, 9.9), c.iso(u0 + 6, 33, 8.4), c.iso(u0, 33, 8.4)], t["glass2"], t["ink2"], .8)
    # ribbon windows on front (y=38) wall
    for i in range(7):
        u0 = 9 + i * 9
        c.winF(38, u0, u0 + 6, 4.6, 6.6, grid=2)
    # loading doors on front
    c.winF(38, 54, 60, 0, 5.2, fill=t["door"], grid=1.2)
    c.winF(38, 63, 69, 0, 5.2, fill=t["door"], grid=1.2)
    # end wall (x=72) windows
    for i in range(3):
        v0 = 8 + i * 9
        c.winS(72, v0, v0 + 6, 4.6, 6.6, grid=2)
    # 2-storey office block in front-left corner: 14 x 10, h 7.2, glass corner
    c.box(6, 38, 14, 10, 0, 7.2, fillF=t["stone"], fillS=t["stone"])
    c.winF(48, 7, 19, 0.6, 3.2, grid=1.5)
    c.winF(48, 7, 19, 4.0, 6.6, grid=1.5)
    c.winS(20, 39, 47, 0.6, 3.2, grid=1.5)
    c.winS(20, 39, 47, 4.0, 6.6, grid=1.5)
    # canopy
    c.poly([c.iso(4, 48, 3.6), c.iso(21, 48, 3.6), c.iso(21, 51, 3.6), c.iso(4, 51, 3.6)], t["roof2"], t["ink"], 1)
    # trees & cars
    for (x, y) in [(2, 10), (2, 20), (2, 30), (30, 42.5), (40, 42.5), (76, 12), (76, 24), (76, 36)]:
        c.tree(x, y)
    # labels
    c.label_iso(39, 21, 12.4, "ÜRETİM HOLÜ · 66 × 34 m", 13)
    c.label_iso(13, 43, 9.2, "İDARİ BLOK", 11)
    c.label_iso(61, 39, 7.4, "YÜKLEME", 10)
    c.north(1500, 90)
    c.text(60, 70, "DEKOR SAFARİ FABRİKASI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Aksonometrik Görünüş — Kuzeydoğu", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Eskişehir OSB · 2.282 m² · Çelik konstrüksiyon üretim holü + 2 katlı idari blok", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Dekor Safari Fabrikası", "Aksonometri · 01/02")
    c.render(path, "Dekor Safari Fabrikası — aksonometrik konsept çizimi")

# ---------------------------------------------------------------- 1b) DEKOR SAFARI — ön cephe
def dekor_safari_elev(theme, path):
    c = Canvas(1600, 900, theme, 1, 0, 0)
    t = c.t
    s = 18.4  # px per m
    gx, gy = 90, 650  # ground line origin
    def P(x, z): return (gx + x * s, gy - z * s)
    # ground
    c.line((60, gy), (1540, gy), t["ink"], 2)
    for k in range(60, 1540, 14):
        c.line((k, gy), (k - 8, gy + 8), t["ink2"], .7, op=.6)
    # hall end wall gable (34 m wide) seen from front? Front (long) elevation: 66 m long, eave 8, ridge 10.6 -> show long side w/ office in front-left
    W, H, HR = 66, 8, 10.6
    c.poly([P(14, 0), P(14 + W, 0), P(14 + W, H), P(14, H)], t["wallF"])
    # roof band (visible slope thickness)
    c.poly([P(13, H), P(15 + W, H), P(15 + W, H + .5), P(13, H + .5)], t["roof"])
    c.poly([P(13, H + .5), P(15 + W, H + .5), P(14 + W, HR + .4), P(14, HR + .4)], t["roof2"], t["ink"], 1)
    # roof lights
    for i in range(6):
        u = 20 + i * 10
        c.poly([P(u, H + 1.0), P(u + 6, H + 1.0), P(u + 6, H + 1.6), P(u, H + 1.6)], t["glass2"], t["ink2"], .8)
    # ribbon windows
    for i in range(7):
        u = 17 + i * 9
        c.rect(*P(u, 6.6), 6 * s, 2 * s, t["glass"], t["ink"], .9)
        c.line(P(u + 3, 4.6), P(u + 3, 6.6), t["ink2"], .5)
        c.line(P(u, 5.6), P(u + 6, 5.6), t["ink2"], .5)
    # cladding joints
    for i in range(1, 22):
        c.line(P(14 + i * 3, 0), P(14 + i * 3, H), t["ink2"], .35, op=.5)
    # loading doors
    for u in (62, 71):
        c.rect(*P(u, 5.2), 6 * s, 5.2 * s, t["door"], t["ink"], 1)
        for k in range(1, 5):
            c.line(P(u, k * 1.05), P(u + 6, k * 1.05), t["ink2"], .5)
    # office block (front-left) 14 x 7.2 stone with glass
    c.rect(*P(14, 7.2), 14 * s, 7.2 * s, t["stone"], t["ink"], 1.3)
    for i in range(1, 7):
        c.line(P(14, i * 1.2), P(28, i * 1.2), t["ink2"], .4, op=.6)
    c.rect(*P(15, 3.2), 12 * s, 2.6 * s, t["glass"], t["ink"], .9)
    c.rect(*P(15, 6.6), 12 * s, 2.6 * s, t["glass"], t["ink"], .9)
    for k in range(1, 8):
        c.line(P(15 + k * 1.5, .6), P(15 + k * 1.5, 3.2), t["ink2"], .5)
        c.line(P(15 + k * 1.5, 4.0), P(15 + k * 1.5, 6.6), t["ink2"], .5)
    c.rect(*P(12.5, 3.7), 17 * s, .35 * s, t["roof2"], t["ink"], 1)  # canopy
    # entrance door
    c.rect(*P(20, 2.6), 2 * s, 2.6 * s, t["door"], t["ink"], 1)
    # trees
    for x in (5, 9, 86, 91):
        c.line(P(x, 0), P(x, 3), t["ink2"], 1.2)
        c.ellipse(*P(x, 4.6), 1.9 * s, 1.7 * s, t["green"], t["ink2"], .9)
    # people scale
    for x in (33, 34.2):
        c.line(P(x, 0), P(x, 1.7), t["ink"], 1.6)
        c.circle(*P(x, 1.95), 3.2, t["ink"], t["ink"], 1)
    # dimension line
    dz = gy + 40
    c.line((P(14, 0)[0], dz), (P(80, 0)[0], dz), t["gold"], 1)
    for x in (14, 28, 80):
        c.line((P(x, 0)[0], dz - 6), (P(x, 0)[0], dz + 6), t["gold"], 1)
    c.text((P(14, 0)[0] + P(28, 0)[0]) / 2, dz - 8, "14,00", 11, t["gold"], "middle", 600, "sans")
    c.text((P(28, 0)[0] + P(80, 0)[0]) / 2, dz - 8, "52,00", 11, t["gold"], "middle", 600, "sans")
    c.text(P(80, 0)[0] + 10, dz + 4, "66,00 m", 11, t["gold"], "start", 600, "sans")
    # height dims
    hx = P(82, 0)[0] + 40
    c.line((hx, gy), (hx, P(0, HR + .4)[1]), t["gold"], 1)
    for z in (0, H, HR + .4):
        c.line((hx - 6, P(0, z)[1]), (hx + 6, P(0, z)[1]), t["gold"], 1)
    c.text(hx + 10, P(0, H)[1] + 4, "+8,00", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, P(0, HR + .4)[1] + 4, "+11,00", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, gy + 4, "±0,00", 11, t["gold"], "start", 600, "sans")
    c.text(60, 70, "DEKOR SAFARİ FABRİKASI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Güney Cephesi", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Trapez sac cephe · şerit pencere · çatı ışıklıkları · taş kaplamalı idari blok", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Dekor Safari Fabrikası", "Güney cephesi · 02/02")
    c.render(path, "Dekor Safari Fabrikası — güney cephesi konsept çizimi")

# ---------------------------------------------------------------- 2) ADEC LSS OSB — aksonometri (cam köşeli üretim + ofis)
def adec_lss_axo(theme, path, anim=False, hero=False):
    c = Canvas(1600, 900, theme, 11.5 if not hero else 12.6, 800, 250 if not hero else 240, anim)
    t = c.t
    c.ground(-8, -8, 74, 46)
    c.poly([c.iso(-8, 40, 0), c.iso(74, 40, 0), c.iso(74, 46, 0), c.iso(-8, 46, 0)], t["door"], t["ink2"], .8)
    c.hedge(0, -4, 68, -4)
    # main 3-storey block 40 x 28 x 12  (front-left glass corner)
    c.box(4, 4, 40, 28, 0, 12, fillF=t["stone"], fillS=t["stone"])
    # stone joints on right (x=44) face
    for k in range(1, 12):
        c.line(c.iso(44, 4, k), c.iso(44, 32, k), t["ink2"], .35, op=.5)
    # glass curtain wall on front (y=32): x 4..30, full height; and wrapping to x1? corner glass on x=4 side not visible -> emphasize front
    c.winF(32, 5, 30, 0.4, 11.4, grid=2.2)
    # gold mullion accents
    for u in (5, 30):
        c.line(c.iso(u, 32, 0.4), c.iso(u, 32, 11.4), t["gold"], 1.4)
    # stone part of front (x 30..44) with slot windows
    for i in range(3):
        c.winF(32, 32 + i * 4, 34 + i * 4, 8.2, 10.6, grid=1.2)
    # roll-up door on right face (x=44)
    c.winS(44, 8, 14, 0, 4.4, fill=t["door"], grid=1.1)
    # brick pilasters at right face ends
    c.box(44, 30, 1.2, 2.4, 0, 12.4, fillF=t["brick"], fillS=t["brick"], fillT=t["brick"])
    c.box(44, 4, 1.2, 2.4, 0, 12.4, fillF=t["brick"], fillS=t["brick"], fillT=t["brick"])
    # production wing behind (right/back): 26 x 24 x 9 with gable
    c.gable(44, 4, 26, 24, 0, 8, 10, "x", fillF=t["wallF"], fillS=t["wallS"])
    for i in range(3):
        v0 = 6 + i * 6
        c.winS(70, v0, v0 + 4, 4.8, 6.8, grid=2)
    # parapet line on main block
    c.poly([c.iso(4, 4, 12), c.iso(44, 4, 12), c.iso(44, 32, 12), c.iso(4, 32, 12)], t["roof"], t["ink"], 1.3)
    # roof units
    for (x, y) in [(10, 10), (18, 10), (26, 10)]:
        c.box(x, y, 4, 3, 12, 1.4, fillF=t["wallS"], fillS=t["wallS"], fillT=t["roof2"])
    # plaza paving lines
    for k in range(0, 40, 3):
        c.line(c.iso(k, 33, 0), c.iso(k, 40, 0), t["ink2"], .3, op=.5)
    # truck & people (scale)
    c.box(50, 34, 6.5, 2.4, 0, 2.6, fillF=t["wallS"], fillS=t["wallF"], fillT=t["roof2"])
    c.box(56.5, 34, 2.2, 2.4, 0, 2.2, fillF=t["glass"], fillS=t["glass2"], fillT=t["roof2"])
    for (x, y) in [(-4, 10), (-4, 20), (-4, 30), (20, 36.5), (32, 36.5), (72, 12), (72, 24)]:
        c.tree(x, y)
    c.label_iso(30, 24, 14.6, "OFİS & ÜRETİM · 40 × 28 m", 13)
    c.label_iso(57, 16, 12.2, "ÜRETİM HOLÜ · 26 × 24 m", 11)
    c.label_iso(17, 34.5, 0.9, "GİYDİRME CAM CEPHE", 10)
    c.north(1500, 90)
    c.text(60, 70, "ADEC LSS FABRİKASI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Aksonometrik Görünüş — Güneydoğu", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Milas OSB · 4.000 m² · Cam köşeli 3 katlı ofis-üretim bloğu + çelik üretim holü", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Adec LSS Fabrikası", "Aksonometri · 01/02")
    c.render(path, "Adec LSS Fabrikası — aksonometrik konsept çizimi")

def adec_lss_elev(theme, path):
    c = Canvas(1600, 900, theme, 1, 0, 0)
    t = c.t
    s = 20.5
    gx, gy = 150, 660
    def P(x, z): return (gx + x * s, gy - z * s)
    c.line((60, gy), (1540, gy), t["ink"], 2)
    for k in range(60, 1540, 14):
        c.line((k, gy), (k - 8, gy + 8), t["ink2"], .7, op=.6)
    # main block 40 wide x 12 high; glass 0..26, stone 26..40
    c.rect(*P(0, 12), 40 * s, 12 * s, t["stone"], t["ink"], 1.3)
    for i in range(1, 10):
        c.line(P(26, i * 1.2), P(40, i * 1.2), t["ink2"], .4, op=.6)
    c.rect(*P(0.6, 11.4), 25.4 * s, 11 * s, t["glass"], t["ink"], 1)
    for k in range(1, 12):
        c.line(P(0.6 + k * 2.15, .4), P(0.6 + k * 2.15, 11.4), t["ink2"], .55)
    for z in (4.0, 7.7):
        c.line(P(.6, z), P(26, z), t["gold"], 1.3)
    for z in (2.2, 5.9, 9.6):
        c.line(P(.6, z), P(26, z), t["ink2"], .5)
    # slot windows on stone
    for i in range(3):
        c.rect(*P(28 + i * 4, 10.6), 2 * s, 2.4 * s, t["glass"], t["ink"], .9)
    # brick pilasters
    c.rect(*P(-1.2, 12.4), 1.2 * s, 12.4 * s, t["brick"], t["ink"], 1)
    c.rect(*P(40, 12.4), 1.2 * s, 12.4 * s, t["brick"], t["ink"], 1)
    for i in range(1, 30):
        c.line(P(-1.2, i * .42), P(0, i * .42), t["ink2"], .35, op=.6)
        c.line(P(40, i * .42), P(41.2, i * .42), t["ink2"], .35, op=.6)
    # roof units
    for x in (6, 14, 22):
        c.rect(*P(x, 13.4), 4 * s, 1.4 * s, t["wallS"], t["ink"], 1)
    # production wing behind, right: 26 wide gable eave 8 ridge 10 (drawn partially behind)
    c.poly([P(41.2, 0), P(67, 0), P(67, 8), P(54, 10), P(41.2, 8)], t["wallF"], t["ink"], 1.2)
    for i in range(3):
        u = 44 + i * 7
        c.rect(*P(u, 6.8), 4 * s, 2 * s, t["glass"], t["ink"], .9)
    c.rect(*P(58, 4.4), 6 * s, 4.4 * s, t["door"], t["ink"], 1)
    for k in range(1, 4):
        c.line(P(58, k * 1.1), P(64, k * 1.1), t["ink2"], .5)
    # entrance
    c.rect(*P(10, 3.0), 3 * s, 3 * s, t["glass2"], t["gold"], 1.3)
    # people
    for x in (16, 17.1, 47):
        c.line(P(x, 0), P(x, 1.7), t["ink"], 1.6)
        c.circle(*P(x, 1.95), 3.2, t["ink"], t["ink"], 1)
    for x in (-8, -4, 72, 76):
        c.line(P(x, 0), P(x, 3), t["ink2"], 1.2)
        c.ellipse(*P(x, 4.6), 1.9 * s, 1.7 * s, t["green"], t["ink2"], .9)
    dz = gy + 40
    c.line((P(0, 0)[0], dz), (P(67, 0)[0], dz), t["gold"], 1)
    for x in (0, 26, 40, 67):
        c.line((P(x, 0)[0], dz - 6), (P(x, 0)[0], dz + 6), t["gold"], 1)
    c.text((P(0, 0)[0] + P(26, 0)[0]) / 2, dz - 8, "26,00", 11, t["gold"], "middle", 600, "sans")
    c.text((P(26, 0)[0] + P(40, 0)[0]) / 2, dz - 8, "14,00", 11, t["gold"], "middle", 600, "sans")
    c.text((P(40, 0)[0] + P(67, 0)[0]) / 2, dz - 8, "27,00", 11, t["gold"], "middle", 600, "sans")
    hx = P(0, 0)[0] - 60
    c.line((hx, gy), (hx, P(0, 12)[1]), t["gold"], 1)
    for z in (0, 4, 7.7, 12):
        c.line((hx - 6, P(0, z)[1]), (hx + 6, P(0, z)[1]), t["gold"], 1)
    c.text(hx - 10, P(0, 12)[1] + 4, "+12,00", 11, t["gold"], "end", 600, "sans")
    c.text(hx - 10, P(0, 7.7)[1] + 4, "+7,70", 11, t["gold"], "end", 600, "sans")
    c.text(hx - 10, P(0, 4)[1] + 4, "+4,00", 11, t["gold"], "end", 600, "sans")
    c.text(hx - 10, gy + 4, "±0,00", 11, t["gold"], "end", 600, "sans")
    c.text(60, 70, "ADEC LSS FABRİKASI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Güney Cephesi", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Giydirme cam cephe · doğal taş kaplama · tuğla pilastrlar · üretim holü", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Adec LSS Fabrikası", "Güney cephesi · 02/02")
    c.render(path, "Adec LSS Fabrikası — güney cephesi konsept çizimi")

# ---------------------------------------------------------------- 3) ADEC LSS AKUAKÜLTÜR — saha aksonometrisi
def adec_aqua_site(theme, path, anim=False, hero=False):
    c = Canvas(1600, 900, theme, 6.4 if not hero else 7.2, 820, 200 if not hero else 190, anim)
    t = c.t
    c.ground(-10, -10, 130, 100)
    # roads (west & south)
    c.poly([c.iso(-10, -10, 0), c.iso(-2, -10, 0), c.iso(-2, 100, 0), c.iso(-10, 100, 0)], t["door"], t["ink2"], .8)
    c.poly([c.iso(-10, 92, 0), c.iso(130, 92, 0), c.iso(130, 100, 0), c.iso(-10, 100, 0)], t["door"], t["ink2"], .8)
    # perimeter hedges
    c.hedge(2, 0, 124, 0); c.hedge(124, 0, 124, 88); c.hedge(2, 88, 124, 88); c.hedge(2, 0, 2, 88)
    # buildings (legend numbering from aerial)
    # 1 Kuluçkahane: 3 small sheds in a row (top-left)
    for i in range(3):
        c.gable(8, 6 + i * 9, 30, 7, 0, 4.2, 5.6, "x")
    # 2 Yavru balık büyütme (left of 1, smaller)
    c.gable(8, 34, 26, 10, 0, 4.5, 6.0, "x")
    # 3 Yavru büyütme + idari — long shed along west-south
    c.gable(10, 50, 70, 10, 0, 4.8, 6.4, "x")
    # 5 RAS 2 — center
    c.gable(46, 12, 42, 16, 0, 5.6, 7.6, "x")
    # 4 RAS 1 — right-center
    c.gable(76, 44, 40, 20, 0, 6.0, 8.2, "x")
    # 6 Balık paketleme — top right
    c.gable(96, 4, 26, 16, 0, 5.2, 7.0, "x")
    # pond (koi) — center-bottom
    px, py = c.iso(62, 74, 0)
    c.ellipse(px, py, 15 * c.s * .9, 8 * c.s * .5, t["water"], t["ink"], 1.2)
    c.ellipse(px - 30, py - 4, 9 * c.s * .6, 4 * c.s * .5, t["water"], "none", 0)
    for (dx, dy) in [(-40, 10), (24, -14), (52, 6), (-58, -6), (10, 20), (42, 18)]:
        c.ellipse(px + dx, py + dy, 9, 6, t["green"], t["ink2"], .8)
    # gravel yard hatch
    for k in range(40, 120, 5):
        c.line(c.iso(k, 30, 0), c.iso(k, 68, 0), t["ink2"], .3, op=.4)
    # trees
    for (x, y) in [(120, 30), (120, 60), (120, 76), (-6, 20), (-6, 60), (30, 84), (100, 84)]:
        c.tree(x, y, 2.6, 4)
    # number tags on roofs
    c.tag(23, 15, 6.4, 1); c.tag(21, 39, 6.8, 2); c.tag(45, 55, 7.2, 3)
    c.tag(96, 54, 9.0, 4); c.tag(67, 20, 8.4, 5); c.tag(109, 12, 7.8, 6)
    # legend box
    lx, ly = 1180, 96
    c.rect(lx, ly, 380, 236, t["paper"], t["gold"], 1.2)
    c.text(lx + 20, ly + 34, "LEJANT", 14, t["gold"], "start", 700, "sans", 3)
    items = ["Kuluçkahane", "Yavru balık büyütme", "Yavru balık büyütme + idari ofisler", "RAS 1 (kapalı devre)", "RAS 2 (kapalı devre)", "Balık paketleme"]
    for i, s in enumerate(items):
        yy = ly + 66 + i * 30
        c.circle(lx + 32, yy - 5, 11, t["bg"], t["ink"], 1.2)
        c.text(lx + 32, yy - 1, str(i + 1), 12, t["ink"], "middle", 700, "sans")
        c.text(lx + 54, yy, s, 13, t["text"], "start", 400, "sans", .3)
    c.text(lx + 20, ly + 258, "37.257119, 27.677975 · Avşar · Milas / Muğla", 10.5, t["ink2"], "start", 400, "sans", .3)
    c.north(1500, 380)
    c.text(60, 70, "ADEC LSS AKUAKÜLTÜR TESİSİ", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Vaziyet Aksonometrisi", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Avşar · Milas / Muğla · 6 yapı · Kuluçkadan paketlemeye kapalı devre balık çiftliği · Kısmen tamamlandı, inşaat devam ediyor", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Adec LSS Akuakültür Tesisi", "Vaziyet aksonometrisi · 01/02")
    c.render(path, "Adec LSS Akuakültür Tesisi — vaziyet aksonometrisi konsept çizimi")

def adec_aqua_section(theme, path):
    """RAS holü enine kesit: tanklar, biyofiltre, ışıklık"""
    c = Canvas(1600, 900, theme, 1, 0, 0)
    t = c.t
    s = 46
    gx, gy = 260, 640
    def P(x, z): return (gx + x * s, gy - z * s)
    # ground & foundation
    c.line((60, gy), (1540, gy), t["ink"], 2)
    for k in range(60, 1540, 14):
        c.line((k, gy), (k - 8, gy + 8), t["ink2"], .7, op=.6)
    c.rect(*P(-1, -0.0), 22 * s, .6 * s, t["wallS"], t["ink"], 1)  # slab
    # walls (20 m span), eave 6, ridge 8.2
    W, H, HR = 20, 6.0, 8.2
    c.poly([P(0, 0), P(W, 0), P(W, H), P(W / 2, HR), P(0, H)], t["wallF"], t["ink"], 1.4)
    # roof thickness line and rooflight at ridge
    c.poly([P(-0.6, H - .1), P(W / 2, HR + .35), P(W + .6, H - .1), P(W + .6, H - .45), P(W / 2, HR), P(-0.6, H - .45)], t["roof"], t["ink"], 1)
    c.poly([P(W / 2 - 2, HR - .6), P(W / 2 + 2, HR - .6), P(W / 2 + 2.2, HR + .4), P(W / 2 - 2.2, HR + .4)], t["glass2"], t["ink"], 1)
    # steel frame lines
    c.line(P(0, 0), P(0, H), t["ink"], 2.2); c.line(P(W, 0), P(W, H), t["ink"], 2.2)
    c.line(P(0, H), P(W / 2, HR), t["ink"], 2.2); c.line(P(W, H), P(W / 2, HR), t["ink"], 2.2)
    c.line(P(3, H + .55), P(W - 3, H + .55), t["ink2"], 1.2)  # tie
    # round tanks (section = rectangles with water)
    for i, x in enumerate((1.4, 6.4, 11.4)):
        c.rect(*P(x, 2.0), 4 * s, 2 * s, t["wallS"], t["ink"], 1.3)
        c.rect(*P(x + .15, 1.7), 3.7 * s, 1.55 * s, t["water"], "none", 0)
        c.line(P(x + .15, 1.7), P(x + 3.85, 1.7), t["ink2"], .8)
        c.text(*P(x + 2, 3.5), "Ø 4 m TANK", 10, t["gold"], "middle", 600, "sans", 1)
    # biofilter / drum filter unit
    c.rect(*P(16.4, 2.6), 2.4 * s, 2.6 * s, t["stone"], t["ink"], 1.2)
    c.circle(*P(17.6, 1.3), .9 * s, t["glass2"], t["ink"], 1)
    c.text(*P(17.6, 3.3), "BİYOFİLTRE", 10, t["gold"], "middle", 600, "sans", 1)
    # pipework
    c.line(P(1.4, 2.35), P(18.8, 2.35), t["gold"], 1.6)
    c.line(P(18.8, 2.35), P(18.8, 0.3), t["gold"], 1.6)
    c.line(P(0.3, 0.3), P(18.8, 0.3), t["gold"], 1.2, dash="6 4")
    for x in (3.4, 8.4, 13.4):
        c.line(P(x, 0.3), P(x, 2.0), t["gold"], 1.2, dash="6 4")
    # blower / aeration
    c.text(*P(10.4, 2.75), "DÖNÜŞ / BESLEME HATTI", 9, t["gold"], "middle", 600, "sans", 1)
    # people
    c.line(P(14.6, .6), P(14.6, 2.3), t["ink"], 1.6); c.circle(*P(14.6, 2.55), 3.2, t["ink"], t["ink"], 1)
    # dims
    dz = gy + 44
    c.line((P(0, 0)[0], dz), (P(W, 0)[0], dz), t["gold"], 1)
    for x in (0, W):
        c.line((P(x, 0)[0], dz - 6), (P(x, 0)[0], dz + 6), t["gold"], 1)
    c.text((P(0, 0)[0] + P(W, 0)[0]) / 2, dz - 8, "20,00 m", 11, t["gold"], "middle", 600, "sans")
    hx = P(W, 0)[0] + 60
    c.line((hx, gy), (hx, P(0, HR)[1]), t["gold"], 1)
    for z in (0, 2, H, HR):
        c.line((hx - 6, P(0, z)[1]), (hx + 6, P(0, z)[1]), t["gold"], 1)
    c.text(hx + 10, P(0, HR)[1] + 4, "+8,20", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, P(0, H)[1] + 4, "+6,00", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, P(0, 2)[1] + 4, "+2,00 su seviyesi", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, gy + 4, "±0,00", 11, t["gold"], "start", 600, "sans")
    c.text(60, 70, "ADEC LSS AKUAKÜLTÜR TESİSİ", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "RAS Holü — Enine Kesit", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Kapalı devre (RAS) yetiştirme holü · Ø 4 m tanklar · biyofiltre · sırt ışıklığı · çelik makas", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Adec LSS Akuakültür Tesisi", "RAS holü kesiti · 02/02")
    c.render(path, "Adec LSS Akuakültür Tesisi — RAS holü kesit konsept çizimi")

# ---------------------------------------------------------------- 4) Akvaryum tüneli (perspektif, koyu)
def aquarium_tunnel(theme, path):
    c = Canvas(1600, 900, theme, 1, 0, 0)
    t = c.t
    cx, cy = 800, 520
    # concentric arches = tunnel rings
    for i in range(9, 0, -1):
        k = i / 9
        rx, ry = 120 + 640 * k, 90 + 470 * k
        fill = t["water"] if i % 2 == 0 else t["glass2"]
        ink = t["ink"]; fo = 0.22 + 0.06 * i
        c.el.append(f'<path d="M {cx-rx:.1f} {cy+ry*0.55:.1f} A {rx:.1f} {ry:.1f} 0 0 1 {cx+rx:.1f} {cy+ry*0.55:.1f} L {cx+rx:.1f} {cy+ry*0.55+40*k:.1f} L {cx-rx:.1f} {cy+ry*0.55+40*k:.1f} Z" fill="{fill}" fill-opacity="{fo:.2f}" stroke="{ink}" stroke-width="1.1" stroke-opacity=".9" pathLength="1"/>')
    # floor / walkway
    c.poly([(cx - 760, 900), (cx + 760, 900), (cx + 110, cy + 60), (cx - 110, cy + 60)], t["paper"], t["ink"], 1.2)
    for k in range(1, 9):
        f = k / 9
        y = cy + 60 + (900 - cy - 60) * f * f
        w = 110 + 650 * f * f
        c.line((cx - w, y), (cx + w, y), t["ink2"], .6, op=.6)
    c.line((cx - 110, cy + 60), (cx - 760, 900), t["gold"], 1.2)
    c.line((cx + 110, cy + 60), (cx + 760, 900), t["gold"], 1.2)
    # fish silhouettes (simple)
    def fish(x, y, L, flip=False):
        d = -1 if flip else 1
        ink2 = t["ink2"]
        c.el.append(f'<path d="M {x} {y} q {d*L*0.5} {-L*0.32} {d*L} 0 q {-d*L*0.5} {L*0.32} {-d*L} 0 z M {x+d*L} {y} l {d*L*0.28} {-L*0.22} l 0 {L*0.44} z" fill="{ink2}" fill-opacity=".85" stroke="none" pathLength="1"/>')
    for (x, y, L, f) in [(300, 250, 70, False), (1240, 300, 90, True), (420, 420, 44, True), (1080, 150, 56, False), (700, 180, 38, True), (960, 460, 30, False), (250, 560, 60, False), (1350, 520, 48, True)]:
        fish(x, y, L, f)
    # light rays
    for x in range(200, 1500, 130):
        g2 = t["gold2"]
        c.el.append(f'<line x1="{x}" y1="0" x2="{x+90}" y2="{cy}" stroke="{g2}" stroke-width="18" stroke-opacity=".06" pathLength="1"/>')
    c.text(60, 70, "AKVARYUM MİMARLIĞI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Tünel Akvaryum — Ziyaretçi Perspektifi", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "Akrilik tünel · büyük tonajlı tank · tematik yaşam alanı · konsept eskiz", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Tünel Akvaryum", "Perspektif eskiz", "Konsept eskiz · Ölçeksiz")
    c.render(path, "Tünel akvaryum — perspektif konsept eskizi")

if __name__ == "__main__":
    print("Üretiliyor:")
    dekor_safari_axo("light", f"{OUT}/dekor-safari-axo.svg")
    dekor_safari_elev("light", f"{OUT}/dekor-safari-elev.svg")
    adec_lss_axo("light", f"{OUT}/adec-lss-axo.svg")
    adec_lss_elev("light", f"{OUT}/adec-lss-elev.svg")
    adec_aqua_site("light", f"{OUT}/adec-aqua-site-axo.svg")
    adec_aqua_section("light", f"{OUT}/adec-aqua-ras-section.svg")
    # dark hero variants
    adec_lss_axo("dark", f"{OUT}/hero-adec-lss-dark.svg", hero=True)
    adec_aqua_site("dark", f"{OUT}/hero-adec-aqua-dark.svg", hero=True)
    dekor_safari_axo("dark", f"{OUT}/hero-dekor-safari-dark.svg", hero=True)
    aquarium_tunnel("dark", f"{OUT}/aquarium-tunnel-dark.svg")
    # animated "video" line-draw
    adec_lss_axo("light", f"{OUT}/anim-adec-lss-draw.svg", anim=True)
    adec_aqua_site("light", f"{OUT}/anim-adec-aqua-draw.svg", anim=True)
    print("Tamam.")

# ---------------------------------------------------------------- 5) Akvaryum — ana tank & tünel kesiti (2. açı)
def aquarium_section(theme, path):
    c = Canvas(1600, 900, theme, 1, 0, 0)
    t = c.t
    s = 34
    gx, gy = 200, 700
    def P(x, z): return (gx + x * s, gy - z * s)
    c.line((60, gy), (1540, gy), t["ink"], 2)
    for k in range(60, 1540, 14):
        c.line((k, gy), (k - 8, gy + 8), t["ink2"], .7, op=.6)
    # building envelope 34 m wide, 14 m high, flat roof w/ skylight
    c.poly([P(0, 0), P(34, 0), P(34, 14), P(0, 14)], t["wallF"], t["ink"], 1.4)
    c.rect(*P(-0.6, 14.6), 35.2 * s, .6 * s, t["roof"], t["ink"], 1)
    c.rect(*P(13, 15.2), 8 * s, .6 * s, t["glass2"], t["ink"], 1)
    # main tank: 20 m wide, 9 m deep water, RC walls
    c.rect(*P(6, 10), 22 * s, 10 * s, t["wallS"], t["ink"], 1.6)
    c.rect(*P(6.8, 9.2), 20.4 * s, 9.2 * s, t["water"], "none", 0)
    c.line(P(6.8, 9.2), P(27.2, 9.2), t["ink2"], .9)
    # acrylic tunnel (arch) inside tank bottom, walkway below floor level
    c.el.append(f'<path d="M {P(12,0)[0]:.1f} {P(12,0)[1]:.1f} L {P(12,2.4)[0]:.1f} {P(12,2.4)[1]:.1f} A {3.5*s:.1f} {3.2*s:.1f} 0 0 1 {P(19,2.4)[0]:.1f} {P(19,2.4)[1]:.1f} L {P(19,0)[0]:.1f} {P(19,0)[1]:.1f} Z" fill="{t["paper"]}" stroke="{t["ink"]}" stroke-width="1.6" pathLength="1"/>')
    c.el.append(f'<path d="M {P(12.5,0)[0]:.1f} {P(12.5,0)[1]:.1f} L {P(12.5,2.3)[0]:.1f} {P(12.5,2.3)[1]:.1f} A {3.0*s:.1f} {2.7*s:.1f} 0 0 1 {P(18.5,2.3)[0]:.1f} {P(18.5,2.3)[1]:.1f} L {P(18.5,0)[0]:.1f} {P(18.5,0)[1]:.1f}" fill="none" stroke="{t["gold"]}" stroke-width="1.3" stroke-dasharray="5 4" pathLength="1"/>')
    c.text(*P(15.5, 1.1), "AKRİLİK TÜNEL", 10, t["gold"], "middle", 600, "sans", 1)
    # viewing gallery left: floor at 0, big acrylic panel
    c.rect(*P(6, 6), .5 * s, 6 * s, t["glass2"], t["gold"], 1.2)
    c.text(*P(3, 6.8), "İZLEME", 10, t["gold"], "middle", 600, "sans", 1)
    c.text(*P(3, 6.0), "GALERİSİ", 10, t["gold"], "middle", 600, "sans", 1)
    # upper walkway / mezzanine right
    c.rect(*P(28, 10.4), 6 * s, .4 * s, t["wallS"], t["ink"], 1)
    c.text(*P(31, 11.3), "TEKNİK MAHAL", 9, t["gold"], "middle", 600, "sans", 1)
    # LSS plant room right ground
    c.rect(*P(29, 3.2), 4 * s, 3.2 * s, t["stone"], t["ink"], 1.1)
    c.circle(*P(31, 1.6), 1.1 * s, t["glass2"], t["ink"], 1)
    c.text(*P(31, 4.1), "LSS · FİLTRASYON", 9, t["gold"], "middle", 600, "sans", 1)
    c.line(P(27.2, 8.6), P(31, 8.6), t["gold"], 1.4); c.line(P(31, 8.6), P(31, 3.2), t["gold"], 1.4)
    # rockwork & fish
    for (x, w) in ((7.2, 4), (22, 5)):
        c.poly([P(x, 0.8), P(x + w, 0.8), P(x + w * .7, 3.0), P(x + w * .3, 2.4)], t["stone"], t["ink2"], .9)
    ink2 = t["ink2"]
    for (x, z, L, d) in ((10, 6.5, 1.6, 1), (17, 7.6, 1.2, -1), (21, 5.2, 2.2, 1), (14, 4.2, 1.0, -1), (24, 7.0, 1.4, -1)):
        X, Z = P(x, z); Lp = L * s
        c.el.append(f'<path d="M {X} {Z} q {d*Lp*0.5} {-Lp*0.32} {d*Lp} 0 q {-d*Lp*0.5} {Lp*0.32} {-d*Lp} 0 z M {X+d*Lp} {Z} l {d*Lp*0.28} {-Lp*0.22} l 0 {Lp*0.44} z" fill="{ink2}" fill-opacity=".85" pathLength="1"/>')
    # people
    for x in (3.2, 15.5, 30.5):
        c.line(P(x, 0), P(x, 1.7), t["ink"], 1.6); c.circle(*P(x, 1.95), 3.2, t["ink"], t["ink"], 1)
    # dims
    dz = gy + 44
    c.line((P(6, 0)[0], dz), (P(28, 0)[0], dz), t["gold"], 1)
    for x in (6, 28): c.line((P(x, 0)[0], dz - 6), (P(x, 0)[0], dz + 6), t["gold"], 1)
    c.text((P(6, 0)[0] + P(28, 0)[0]) / 2, dz - 8, "22,00 m ANA TANK", 11, t["gold"], "middle", 600, "sans")
    hx = P(34, 0)[0] + 60
    c.line((hx, gy), (hx, P(0, 14)[1]), t["gold"], 1)
    for z in (0, 9.2, 14): c.line((hx - 6, P(0, z)[1]), (hx + 6, P(0, z)[1]), t["gold"], 1)
    c.text(hx + 10, P(0, 14)[1] + 4, "+14,00", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, P(0, 9.2)[1] + 4, "+9,20 su seviyesi", 11, t["gold"], "start", 600, "sans")
    c.text(hx + 10, gy + 4, "±0,00", 11, t["gold"], "start", 600, "sans")
    c.text(60, 70, "AKVARYUM MİMARLIĞI", 13, t["gold"], "start", 600, "sans", 3)
    c.text(60, 108, "Ana Tank & Tünel — Enine Kesit", 30, t["text"], "start", 400, "serif")
    c.text(60, 134, "≈ 1.800 m³ ana tank · akrilik tünel · izleme galerisi · LSS filtrasyon · konsept kesit", 13, t["ink2"], "start", 400, "sans", .3)
    c.title("Tünel Akvaryum", "Kesit · 02/02", "Konsept çizim · Ölçeksiz")
    c.render(path, "Tünel akvaryum — ana tank ve tünel enine kesit konsept çizimi")

aquarium_section("light", f"{OUT}/aquarium-section.svg")
aquarium_tunnel("light", f"{OUT}/aquarium-tunnel-light.svg")
