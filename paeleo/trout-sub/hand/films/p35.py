"""p35 · Post #44 · a document montage on a pinboard.

Lineage: the 1940s documentary photograph file (FSA/OWI, Library of Congress). Method: prints laid
on a board and pinned, each with its typed slip; a paper mailbox numbered 44 drawn, cut and pinned
over them; a sheet of green gel pulled across for the river; a canvas mail sack scissored out of
Russell Lee's 1940 print and hung from the box; letters dealt as cut paper.
Rule: Fixed-Shot Handoff. Each part is one locked shot, and everything that happens in it is a
thing passing from one holder to the next: table to board, sack to trout, trout to tin.

    python3 films/p35.py --forage      fetch the photographs and write films/credits/p35.json
    python3 films/p35.py --stills 2 6  stills + contact sheet
    python3 films/p35.py               render assets/films/p35.mp4
"""
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from kit import *  # noqa
from kit_anim import contact

SLUG = "p35"
T1, T2, SECONDS = 14.0, 24.0, 34.0
SRC = HERE / "sources" / SLUG
CREDITS = HERE / "credits" / f"{SLUG}.json"
WW, WH = 1920, 1080                 # the table, in table pixels (2 per screen pixel in the wide shot)
A = {}                              # built assets


# ================================================================ small tools ===

def vnoise(shape, scale, seed=0, octaves=1, sy=None):
    """Smooth value noise in 0..1."""
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    rs = np.random.RandomState(seed)
    sx, sy = float(scale), float(sy or scale)
    for _ in range(octaves):
        gw, gh = max(2, int(w / sx) + 2), max(2, int(h / sy) + 2)
        g = Image.fromarray((rs.rand(gh, gw) * 255).astype(np.uint8))
        out += amp * np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 255.0
        tot += amp
        amp *= 0.5
        sx, sy = max(1.0, sx / 2), max(1.0, sy / 2)
    return out / tot


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def catmull(pts, per=8, closed=False):
    pts = [np.array(p, np.float32) for p in pts]
    if closed:
        pts = [pts[-1]] + pts + pts[:2]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            s = k / per
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3)))
    if not closed:
        out.append(tuple(pts[-2]))
    return out


def keys(t, ks):
    """Piecewise eased keyframes [(t, v...), ...] -> tuple of values."""
    if t <= ks[0][0]:
        return ks[0][1:]
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            f = smooth((t - a[0]) / max(1e-6, b[0] - a[0]))
            return tuple(lerp(x, y, f) for x, y in zip(a[1:], b[1:]))
    return ks[-1][1:]


def spring(t, t0, amp, freq=3.2, damp=4.0):
    """A released thing: damped swing after t0."""
    if t < t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-damp * u) * math.cos(2 * math.pi * freq * u)


def twos(t):
    """Cutout animation is shot on twos: hold each position for two frames."""
    return math.floor(t * 12) / 12.0


# ================================================================== materials ===

def paper_tex(w, h, color, seed=0, grain=0.05, fibre=0.035, mottle=0.04):
    rs = np.random.RandomState(seed)
    a = np.ones((h, w, 3), np.float32) * np.array(color, np.float32)
    g = rs.normal(0, 1, (h, w)).astype(np.float32)
    g = np.asarray(Image.fromarray(np.clip(g * 40 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 128 - 1
    fb = (vnoise((h, w), 26, seed + 1, 2, sy=2.5) - 0.5) * 2
    mo = (vnoise((h, w), 120, seed + 2, 3) - 0.5) * 2
    a *= (1 + grain * g + fibre * fb + mottle * mo)[..., None]
    return a


def bevel(img, light=34, dark=46, d=1):
    """A cut edge has thickness: the edge toward the lamp (upper left) catches light, the far edge is in shade."""
    al = np.asarray(img.getchannel("A"), np.float32) / 255
    up = np.roll(np.roll(al, d, 0), d, 1)
    dn = np.roll(np.roll(al, -d, 0), -d, 1)
    hi = np.clip(al - up, 0, 1)
    lo = np.clip(al - dn, 0, 1)
    a = np.asarray(img, np.float32).copy()
    a[..., :3] += (hi * light - lo * dark)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def cut_paper(tex, mask, edge=True):
    im = to_img(tex).convert("RGBA")
    im.putalpha(mask)
    return bevel(im) if edge else im


def poly_mask(size, pts, blur=0.6):
    S = 2
    m = Image.new("L", (size[0] * S, size[1] * S), 0)
    ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in pts], fill=255)
    return m.resize(size, Image.LANCZOS)


def wobbly(pts, amt=1.2, seed=0):
    """Scissors do not cut ruler-straight: nudge each vertex."""
    rs = np.random.RandomState(seed)
    return [(x + rs.uniform(-amt, amt), y + rs.uniform(-amt, amt)) for x, y in pts]


def shadow_of(img, blur, opacity, color=(18, 12, 6)):
    al = img.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    sh = Image.new("RGBA", img.size, color + (0,))
    sh.putalpha(al)
    return sh


def lay(cv, img, x, y, rot=0.0, lift=1.0, scale=1.0, alpha=1.0, shadow=True, pivot=None):
    """Lay a cut piece on the table, centred on (x, y) (or with its pivot there). lift = height above
    the table in table pixels: the higher, the further and softer its shadow falls (lamp upper left)."""
    im = img
    if scale != 1.0:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.LANCZOS)
    cx, cy = im.width / 2, im.height / 2
    px, py = (cx, cy) if pivot is None else (pivot[0] * scale, pivot[1] * scale)
    if abs(rot) > 0.01:
        # rotate about the pivot: expand, then find where the pivot went
        r = math.radians(rot)
        im2 = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        dx, dy = px - cx, py - cy
        qx = im2.width / 2 + dx * math.cos(r) + dy * math.sin(r)
        qy = im2.height / 2 - dx * math.sin(r) + dy * math.cos(r)
        im, px, py = im2, qx, qy
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    ox, oy = int(round(x - px)), int(round(y - py))
    if shadow:
        pad = int(8 + lift * 2.4)
        big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        big.paste(im, (pad, pad))
        sh = shadow_of(big, 1.6 + lift * 0.55, (0.62 if lift < 6 else 0.5) * alpha)
        paste_clip(cv, sh, ox - pad + int(2 + lift * 0.9), oy - pad + int(3 + lift * 1.25))
    paste_clip(cv, im, ox, oy)


def paste_clip(cv, im, ox, oy):
    sx, sy = max(0, -ox), max(0, -oy)
    if sx >= im.width or sy >= im.height or ox >= cv.width or oy >= cv.height:
        return
    if ox + im.width > cv.width or oy + im.height > cv.height:
        im = im.crop((0, 0, min(im.width, cv.width - ox), min(im.height, cv.height - oy)))
    cv.alpha_composite(im, dest=(max(0, ox), max(0, oy)), source=(sx, sy))


# ==================================================================== forage ===
# The lineage is the FSA/OWI file at the Library of Congress, so the prints come from there:
# loc.gov was reachable while this was made, and every item is checked for the Library's own
# rights advisory ("No known restrictions": work made for the U.S. government). The trout and the
# turkey are Wikimedia Commons plates. Downloads are data: decoded with PIL, never run.

LOC_RIGHTS = "https://www.loc.gov/rr/print/res/071_fsab.html"
FORAGE_LOC = [
    # name, LOC item id, service file, used_as
    ("road.jpg", "2017779506", "fsa/8b19000/8b19300/8b19326v.jpg",
     "the big print the paper mailbox is pinned over: a row of rural mailboxes in snow"),
    ("mailbox.jpg", "2017812463", "fsa/8c19000/8c19400/8c19455v.jpg",
     "print: one rural mailbox on its post, the model the paper box is cut after"),
    ("cross.jpg", "2017794296", "fsa/8c05000/8c05300/8c05355v.jpg",
     "print: Jack Delano's two mailboxes at a Georgia crossroads"),
    ("sack.jpg", "2017786080", "fsa/8b24000/8b24500/8b24582v.jpg",
     "print, and from a second copy of it two cutouts: the canvas mail sack that hangs out of the paper mailbox, and the weathered post the mailbox is pinned to"),
    ("postoffice.jpg", "2017786861", "fsa/8b25000/8b25300/8b25314v.jpg",
     "print: a country post office, the postmaster taking a mail sack from the stage"),
]
FORAGE_COMMONS = [
    ("trout.png", "File:Denton Brook Trout 1896.png", 960,
     "the trout residents: cut out of the 1896 plate, flexed along the body"),
    ("turkey.jpg", "File:1 Wild Turkey.jpg", 1280,
     "Turkey: head and neck cut from plate 1 of The Birds of America, the wattle a separate hinged piece"),
]


def _http(url, tries=4):
    """Patient fetch: wait out a Retry-After, never hammer."""
    import urllib.error
    import urllib.request
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "oulipo-film-research/1.0"}), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            err = e
            wait = int(e.headers.get("Retry-After") or 0) if e.code == 429 else 0
            print("  wait", e.code, wait, flush=True)
            time.sleep(min(900, max(wait + 7, 15 + 5 * k)))
        except Exception as e:  # noqa
            err = e
            time.sleep(15 + 5 * k)
    raise err


def commons_page_info(title):
    import html
    import re
    import urllib.parse
    name = title.split(":", 1)[1].replace(" ", "_")
    page = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name)
    h = _http(page).decode("utf8", "ignore").replace("&#95;", "_")

    def spans(cls):
        return [re.sub(r"<[^>]+>", "", html.unescape(x)).strip() for x in re.findall(r'class="%s"[^>]*>(.*?)</span>' % cls, h, flags=re.S)]

    def field(fid):
        m = re.search(r'id="%s".*?<td[^>]*>(.*?)</td>' % fid, h, flags=re.S)
        if not m:
            return ""
        s = re.sub(r"<style.*?</style>", "", m.group(1), flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s))).strip()

    m = re.search(r'fullImageLink.*?href="([^"]+)"', h, flags=re.S)
    full = html.unescape(m.group(1)).split("?")[0]
    if full.startswith("//"):
        full = "https:" + full
    lic = spans("licensetpl_short")
    link = spans("licensetpl_link")
    return dict(title=title, author=field("fileinfotpl_aut")[:120] or "unknown", license=lic[0] if lic else "",
                license_url=link[0] if link else "", source_url=page, file_url=full, date=field("fileinfotpl_date")[:40])


def forage_all():
    from kit_anim import licence_ok
    SRC.mkdir(parents=True, exist_ok=True)
    CREDITS.parent.mkdir(parents=True, exist_ok=True)
    cr = json.loads(CREDITS.read_text()) if CREDITS.exists() else []

    def record(entry):
        nonlocal cr
        cr = [c for c in cr if c["source_url"] != entry["source_url"]]
        cr.append(entry)
        CREDITS.write_text(json.dumps(cr, indent=1, ensure_ascii=False))

    for name, item, path, used in FORAGE_LOC:
        src_url = f"https://www.loc.gov/item/{item}/"
        if (SRC / name).exists() and any(c["source_url"] == src_url for c in cr):
            continue
        j = json.loads(_http(src_url + "?fo=json"))["item"]
        rights = (j.get("rights_advisory") or j.get("rights_information") or "")
        if isinstance(rights, list):
            rights = " ".join(rights)
        if not rights.lower().startswith("no known restrictions"):
            raise SystemExit(f"REJECT rights {rights!r} {item}")
        url = "https://tile.loc.gov/storage-services/service/pnp/" + path
        time.sleep(3)
        if not (SRC / name).exists():
            (SRC / name).write_bytes(_http(url))
        Image.open(SRC / name).verify()
        who = "; ".join(j.get("contributor_names") or ["unknown"])
        record(dict(title=f"{j.get('title')} ({(j.get('date') or '')[:4]}; {j.get('reproduction_number') or j.get('call_number') or ''})",
                    author=who, license="No known restrictions on publication (U.S. Farm Security Administration / Office of War Information photograph, Library of Congress)",
                    license_url=LOC_RIGHTS, source_url=src_url, file_url=url, used_as=used))
        print("foraged", name, "|", j.get("title"), "|", who, "|", rights[:24], flush=True)
        time.sleep(4)
    for name, title, width, used in FORAGE_COMMONS:
        if any(c["title"] == title for c in cr) and (SRC / name).exists():
            continue
        i = commons_page_info(title)
        if not licence_ok(i["license"]):
            raise SystemExit(f"REJECT licence {i['license']!r} {title}")
        base, fn = i["file_url"].split("/commons/", 1)
        url = f"{base}/commons/thumb/{fn}/{width}px-{fn.split('/')[-1]}"
        if not (SRC / name).exists():
            (SRC / name).write_bytes(_http(url))
        Image.open(SRC / name).verify()
        record(dict(title=title, author=i["author"], license=i["license"], license_url=i["license_url"],
                    source_url=i["source_url"], file_url=url, used_as=used))
        print("foraged", name, "|", i["license"], "|", i["author"], flush=True)
        time.sleep(4)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--forage":
    forage_all()
    raise SystemExit(0)


# ============================================================ foraged pieces ===

def src(name):
    p = SRC / name
    if not p.exists():
        if "--stills" in sys.argv:          # work can go on while the archive is slow; a render refuses
            ph = to_img(vnoise((480, 640), 60, 3, 3)[..., None] * np.ones(3) * 200).convert("RGB")
            ImageDraw.Draw(ph).text((20, 20), "MISSING " + name, fill=(255, 0, 0))
            return ph
        raise SystemExit(f"missing foraged file {name}: run  python3 films/p35.py --forage")
    return Image.open(p).convert("RGB")


def biggest(mask):
    from scipy import ndimage as ndi
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return ndi.binary_fill_holes(lab == (1 + int(np.argmax(sizes))))


def typed_strip(lines, seed=0, size=22, color=(226, 213, 182), ink=(38, 34, 40)):
    """A typewritten caption slip: each letter struck a little high or low, some lighter than others."""
    f = font("mono", size)
    rs = np.random.RandomState(seed)
    wmax = max(f.getlength(s) for s in lines)
    w, h = int(wmax + 30), int(len(lines) * size * 1.32 + 16)
    tex = paper_tex(w, h, color, seed + 40, grain=0.04)
    im = to_img(tex).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    for li, s in enumerate(lines):
        x = 15.0
        for ch in s:
            d.text((x + rs.uniform(-0.5, 0.5), 7 + li * size * 1.32 + rs.uniform(-1.0, 1.0)), ch, font=f,
                   fill=ink + (int(rs.uniform(150, 245)),))
            x += f.getlength(ch)
    m = poly_mask((w, h), wobbly([(1, 1), (w - 1, 2), (w - 2, h - 1), (2, h - 2)], 1.0, seed))
    im.putalpha(m)
    return bevel(im, 22, 34)


def make_print(photo, pw, border=20, seed=0, warm=(1.0, 0.975, 0.92)):
    """A gelatin-silver print: the photograph on its white-bordered paper."""
    ph = photo.convert("L").resize((pw, int(pw * photo.height / photo.width)), Image.LANCZOS)
    a = np.asarray(ph, np.float32)
    a = (a - a.min()) / max(1.0, a.max() - a.min()) * 232 + 14          # print blacks are not ink black
    rgb = a[..., None] * np.array(warm, np.float32)
    w, h = pw + 2 * border, ph.height + 2 * border
    sheet = paper_tex(w, h, (240, 236, 226), seed, grain=0.02, fibre=0.01, mottle=0.03)
    sheet[border:border + ph.height, border:border + pw] = rgb
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sheen = np.exp(-(((xx / w - yy / h) - 0.15) / 0.22) ** 2) * 14          # the gloss of the print catching the lamp
    sheet += sheen[..., None]
    curl = 1 - 0.10 * np.clip((yy / h - 0.9) / 0.1, 0, 1) - 0.06 * np.clip((xx / w - 0.94) / 0.06, 0, 1)   # the far corner lifts a little
    sheet *= curl[..., None]
    im = to_img(sheet).convert("RGBA")
    im.putalpha(poly_mask((w, h), [(1, 1), (w - 1, 1), (w - 1, h - 1), (1, h - 1)]))
    return bevel(im, 16, 40)


def trim_rebate(im, inset=5):
    """A scan of a negative carries the black film edge: keep the picture inside it."""
    g = np.asarray(im.convert("L"), np.float32)

    def run(v):
        ok = v > 46
        best, cur, start = (0, 0), 0, 0
        for k, o in enumerate(list(ok) + [False]):
            if o:
                if cur == 0:
                    start = k
                cur += 1
            else:
                if cur > best[1] - best[0]:
                    best = (start, start + cur)
                cur = 0
        return best
    x0, x1 = run(np.median(g[g.shape[0] // 4: 3 * g.shape[0] // 4], axis=0))
    y0, y1 = run(np.median(g[:, g.shape[1] // 4: 3 * g.shape[1] // 4], axis=1))
    return im.crop((x0 + inset, y0 + inset, x1 - inset, y1 - inset))


PRINTS = [   # key, file, width on the board, typed slip
    ("road", "road.jpg", 860, ["MAILBOXES ON RURAL ROAD, MD.", "ROTHSTEIN 1940.  F.S.A."]),
    ("mailbox", "mailbox.jpg", 430, ["RURAL MAILBOX, INDIANA", "VACHON 1941"]),
    ("cross", "cross.jpg", 320, ["O'NIELS CROSSROADS, GA.", "DELANO 1941"]),
    ("sackprint", "sack.jpg", 300, ["MAIL BAG, PINTO CREEK", "LEE 1940"]),
    ("po", "postoffice.jpg", 410, ["POST OFFICE, PIE TOWN", "LEE 1940"]),
]


def build_prints():
    for k, (key, fn, pw, lines) in enumerate(PRINTS):
        A["print_" + key] = make_print(trim_rebate(src(fn)), pw, seed=k + 1)
        A["strip_" + key] = typed_strip(lines, k + 1, 22 if key == "road" else 19)
    A["strip_box"] = typed_strip(["BOX 44: PAPER, CUT HERE"], 6, 19, color=(206, 222, 226))


def build_trout():
    im = src("trout.png")
    a = np.asarray(im, np.float32)
    paper = np.median(np.concatenate([a[:20].reshape(-1, 3), a[-20:].reshape(-1, 3)]), axis=0)
    m = biggest(np.abs(a - paper).sum(2) > 38)
    al = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 0 if v < 120 else min(255, (v - 120) * 4))
    t = im.convert("RGBA")
    t.putalpha(al)
    t = t.crop(al.getbbox())
    A["trout_full"] = t
    w = 236
    A["trout"] = bevel(t.resize((w, int(w * t.height / t.width)), Image.LANCZOS), 30, 40)      # head at left


TURKEY_CUT = [(903, 128), (940, 112), (975, 95), (990, 40), (1003, 28), (1015, 70), (1060, 100), (1120, 140), (1140, 200), (1146, 270),
              (1158, 330), (1182, 390), (1198, 450), (1180, 500), (1100, 470), (1040, 450), (1030, 405), (1040, 350), (1015, 290),
              (1012, 230), (985, 185), (945, 160), (910, 140)]
WATTLE_CUT = [(1040, 345), (1090, 332), (1165, 360), (1174, 402), (1120, 424), (1060, 428), (1026, 405)]
TBOX = (890, 16, 1236, 510)


def build_turkey():
    """Head and neck scissored out of the Audubon plate (the cut line was measured on the 1280 px scan)."""
    from scipy import ndimage as ndi
    im = src("turkey.jpg")
    k = im.width / 1280.0
    a = np.asarray(im, np.float32)
    far = (np.abs(a - np.array([233, 224, 200], np.float32)).sum(2) > 62) | (a.sum(2) < 520)

    def cut(poly):
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in catmull(poly, 5, closed=True)], fill=255)
        keep = biggest(ndi.binary_opening(far & (np.asarray(m) > 0), iterations=1))
        keep = ndi.binary_erosion(keep, iterations=2)
        o = im.convert("RGBA")
        o.putalpha(Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9)))
        return o.crop(tuple(int(v * k) for v in TBOX))
    A["turkey"] = cut(TURKEY_CUT)
    A["wattle"] = cut(WATTLE_CUT)
    A["tk"] = k


def turkey_img(wattle_deg=0.0, height=300):
    base = A["turkey"].copy()
    k = A["tk"]
    pin = ((1085 - TBOX[0]) * k, (345 - TBOX[1]) * k)
    base.alpha_composite(A["wattle"].rotate(wattle_deg, center=pin, resample=Image.BICUBIC))
    return base.resize((int(height * base.width / base.height), height), Image.LANCZOS)


# ============================================================ handmade pieces ===

BLUE = (88, 122, 150)
NAVY = (30, 44, 62)
CREAM = (238, 229, 205)
RED = (168, 44, 40)
KRAFT = (150, 112, 74)


def build_board():
    """The pinboard: cork, lit by one lamp at the upper left, in an oak frame."""
    h, w = WH, WW
    n1, n2, n3 = vnoise((h, w), 5, 1), vnoise((h, w), 12, 2), vnoise((h, w), 2.4, 3)
    big = vnoise((h, w), 320, 4, 3)
    g = np.clip((0.42 * n1 + 0.3 * n2 + 0.28 * n3 - 0.5) * 1.7 + 0.5, 0, 1)
    dark, light = np.array([104, 68, 40], np.float32), np.array([178, 136, 92], np.float32)
    a = dark + (light - dark) * g[..., None]
    a *= (0.88 + 0.24 * big)[..., None]
    pits = ((n3 < 0.3) & (n1 < 0.42)).astype(np.float32)
    pits = np.asarray(Image.fromarray((pits * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    a *= (1 - 0.3 * pits)[..., None]
    rs = np.random.RandomState(7)
    img = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(46):                       # old pin holes
        x, y = rs.uniform(40, w - 40), rs.uniform(40, h - 40)
        d.ellipse([x - 2, y - 2, x + 2.5, y + 2.5], fill=(40, 24, 12, 210))
        d.ellipse([x + 1, y + 1, x + 4, y + 4], fill=(230, 196, 150, 70))
    # oak frame along the top and the left: where the lamp side is
    fr = paper_tex(w, 34, (112, 78, 44), 9, grain=0.05, fibre=0.12, mottle=0.1)
    img.paste(to_img(fr), (0, 0))
    fl = paper_tex(34, h, (104, 72, 40), 10, grain=0.05, fibre=0.02, mottle=0.12)
    img.paste(to_img(fl), (0, 0))
    d.line([(0, 34), (w, 34)], fill=(30, 18, 8, 230), width=3)
    d.line([(34, 34), (34, h)], fill=(30, 18, 8, 230), width=3)
    d.line([(36, 38), (w, 38)], fill=(20, 12, 4, 90), width=6)
    d.line([(39, 38), (39, h)], fill=(20, 12, 4, 90), width=6)
    A["board"] = img
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((xx - 520) / w, (yy - 260) / h)
    A["lamp1"] = (1.12 - 0.62 * np.clip(r, 0, 1) ** 1.5)[..., None].astype(np.float32)


# ---- the mailbox, in the blue sheet's own coordinates (560 x 330) -----------

SHEET = (560, 330)


def body_outline():
    pts = [(455, 268), (300, 270), (150, 268), (100, 266), (80, 248), (76, 200), (76, 130), (84, 92), (108, 70), (150, 62),
           (300, 60), (455, 64)]
    dense = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 6))
        dense += [(lerp(x0, x1, k / n), lerp(y0, y1, k / n)) for k in range(n)]
    rs = np.random.RandomState(44)          # the hand wanders a little off the pencil line
    dense = [(x + rs.uniform(-0.8, 0.8), y + rs.uniform(-0.8, 0.8)) for x, y in dense]
    return dense


OUTLINE = body_outline()
ENTRY = [(560, 300), (520, 290), (485, 278), (455, 268)]      # the scissors come in from the sheet's edge
STROKES = [   # "#44" painted with a loaded brush, one stroke at a time (sheet coordinates)
    [(152, 112), (140, 214)], [(190, 112), (178, 214)], [(118, 146), (212, 146)], [(112, 184), (206, 184)],
    [(292, 108), (246, 180), (318, 180)], [(300, 110), (296, 222)],
    [(396, 108), (350, 180), (422, 180)], [(404, 110), (400, 222)],
]


def path_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def path_at(pts, f):
    """Point and heading at fraction f of a polyline."""
    f = clamp(f)
    total = path_len(pts)
    want = f * total
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + seg >= want and seg > 0:
            u = (want - acc) / seg
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u)), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        acc += seg
    a, b = pts[-2], pts[-1]
    return b, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def path_part(pts, f):
    """The first fraction f of a polyline."""
    f = clamp(f)
    total = path_len(pts)
    want = f * total
    out, acc = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + seg >= want:
            u = (want - acc) / max(seg, 1e-6)
            out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
            return out
        out.append(b)
        acc += seg
    return out


def build_box():
    w, h = SHEET
    tex = paper_tex(w, h, BLUE, 21, grain=0.05, fibre=0.05, mottle=0.06)
    A["sheet_tex"] = tex
    full = poly_mask((w, h), wobbly([(2, 3), (w - 3, 1), (w - 1, h - 3), (1, h - 2)], 1.5, 3))
    A["sheet"] = cut_paper(tex, full)
    bm = poly_mask((w, h), OUTLINE)
    A["body_mask"] = bm
    A["body"] = cut_paper(tex, bm)
    # the waste: the sheet with the box-shaped hole and the slit the scissors came in by
    wm = ImageChops.subtract(full, bm.filter(ImageFilter.MaxFilter(3)))
    dw = ImageDraw.Draw(wm)
    dw.line(ENTRY, fill=0, width=3)
    A["waste"] = cut_paper(tex, wm)
    # mouth: the open end, a dark arch with a blue rim; door: the same arch, cut from the same sheet
    aw, ah = 112, 214

    def arch(inset=0, wd=aw, ht=ah):
        r = wd / 2 - inset
        pts = [(inset, ht - inset), (inset, wd / 2)]
        pts += [(wd / 2 - r * math.cos(math.radians(a)), wd / 2 - r * math.sin(math.radians(a))) for a in range(0, 181, 9)]
        pts += [(wd - inset, ht - inset)]
        return pts
    rim = cut_paper(paper_tex(aw, ah, tuple(int(c * 1.08) for c in BLUE), 22), poly_mask((aw, ah), wobbly(arch(), 0.8, 5)))
    inner = cut_paper(paper_tex(aw, ah, NAVY, 23, grain=0.08), poly_mask((aw, ah), wobbly(arch(11), 0.8, 6)))
    sh = shadow_of(inner, 5, 0.5)
    rim.alpha_composite(inner)
    A["mouth"] = rim
    door = cut_paper(paper_tex(aw, ah, tuple(int(c * 0.9) for c in BLUE), 24), poly_mask((aw, ah), wobbly(arch(2), 0.8, 7)))
    dd = ImageDraw.Draw(door, "RGBA")
    dd.rounded_rectangle([aw / 2 - 9, 30, aw / 2 + 9, 64], radius=5, fill=(60, 86, 110, 255), outline=(30, 44, 60, 220))   # the pull tab, pasted on
    dd.line(arch(9)[1:-1], fill=(40, 60, 84, 150), width=2)          # scored fold line
    A["door"] = door
    A["door_pivot"] = (aw / 2, ah - 6)
    # flag: red card on a stem
    fw, fh = 70, 104
    fm = poly_mask((fw, fh), wobbly([(8, 4), (64, 6), (62, 44), (24, 44), (24, 100), (8, 100)], 0.8, 8))
    A["flag"] = cut_paper(paper_tex(fw, fh, RED, 25, grain=0.06), fm)
    A["flag_pivot"] = (16, 92)
    # post: a strip of brown kraft, the grain ruled on with a soft pencil
    pw, ph = 74, 620
    pt = paper_tex(pw, ph, KRAFT, 26, grain=0.07, fibre=0.02, mottle=0.1)
    grain = vnoise((ph, pw), 5, 27, 2, sy=120)
    pt *= (0.82 + 0.36 * grain)[..., None]
    post = cut_paper(pt, poly_mask((pw, ph), wobbly([(3, 2), (pw - 2, 4), (pw - 5, ph - 2), (1, ph - 3)], 1.4, 9)))
    pd = ImageDraw.Draw(post, "RGBA")
    rs = np.random.RandomState(5)
    for _ in range(9):
        x = rs.uniform(8, pw - 8)
        y0 = rs.uniform(0, ph - 200)
        pd.line([(x + rs.uniform(-3, 3) * k, y0 + k * 40) for k in range(int(rs.uniform(3, 9)))], fill=(70, 46, 26, 130), width=2)
    A["post"] = post


def ink_layer(n_done, part=0.0):
    """The number, as far as the brush has got: n_done whole strokes and `part` of the next."""
    key = ("ink", n_done, round(part, 2))
    if key in A:
        return A[key]
    w, h = SHEET
    S = 2
    lay_ = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(lay_)
    for k, st in enumerate(STROKES[: n_done + 1]):
        f = 1.0 if k < n_done else part
        if f <= 0:
            continue
        pts = catmull(st, 6) if len(st) > 2 else [lerp2(st[0], st[1], q / 10) for q in range(11)]
        pts = path_part(pts, f)
        n = len(pts)
        for q in range(max(1, n - 1)):
            a, b = pts[q], pts[min(n - 1, q + 1)]
            u = q / max(1, n - 1)
            wd = (13 - 5 * u * (f == 1.0 and 1 or 0.6)) * S          # the brush runs dry toward the end of a stroke
            d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=255, width=int(wd))
            d.ellipse([a[0] * S - wd / 2, a[1] * S - wd / 2, a[0] * S + wd / 2, a[1] * S + wd / 2], fill=255)
    m = np.asarray(lay_.resize((w, h), Image.LANCZOS), np.float32) / 255
    dry = 0.72 + 0.28 * (vnoise((h, w), 3, 31, 1, sy=14) > 0.3)       # bristle streaks
    al = np.clip(m * dry * 1.05, 0, 1)
    out = Image.new("RGBA", (w, h), (22, 28, 44, 0))
    out.putalpha(Image.fromarray((al * 255).astype(np.uint8)))
    if part in (0.0, 1.0) or len(A) < 4000:
        A[key] = out
    return out


def body_img(n_done, part=0.0):
    key = ("body", n_done, round(part, 2))
    if key not in A:
        im = A["body"].copy()
        ink = ink_layer(n_done, part)
        ink.putalpha(ImageChops.multiply(ink.getchannel("A"), A["body_mask"]))
        im.alpha_composite(ink)
        A[key] = im
    return A[key]


def sheet_img(drawn, cutf):
    """The blue sheet with the pencil line as far as drawn, and the scissors' cut as far as cut."""
    key = ("sheetimg", round(drawn, 3), round(cutf, 3))
    if key in A:
        return A[key]
    im = A["sheet"].copy()
    d = ImageDraw.Draw(im, "RGBA")
    if drawn > 0:
        loop = OUTLINE + OUTLINE[:1]
        pts = path_part(loop, drawn)
        if len(pts) > 1:
            d.line(pts, fill=(226, 232, 236, 150), width=2)
    if cutf > 0:
        cutpath = ENTRY + OUTLINE[1:] + OUTLINE[:1]
        pts = path_part(cutpath, cutf)
        if len(pts) > 1:
            d.line([(x + 1.5, y + 2) for x, y in pts], fill=(214, 228, 238, 120), width=2)     # the lifted lip of the cut
            d.line(pts, fill=(28, 20, 12, 235), width=3)                                       # the board showing through
    if len(A) < 4000:
        A[key] = im
    return im


def build_letters():
    rs = np.random.RandomState(12)
    w, h = 104, 66
    for k in range(7):
        tex = paper_tex(w, h, tuple(int(c * rs.uniform(0.97, 1.03)) for c in CREAM), 50 + k, grain=0.03, fibre=0.03)
        m = poly_mask((w, h), wobbly([(2, 2), (w - 2, 3), (w - 3, h - 2), (2, h - 3)], 1.0, 60 + k))
        im = cut_paper(tex, m)
        d = ImageDraw.Draw(im, "RGBA")
        if k % 3 != 2:        # the back: flap folds and a red wax seal
            d.line([(3, 4), (w / 2, h * 0.58), (w - 3, 4)], fill=(120, 104, 80, 200), width=2)
            d.line([(3, 5), (w / 2, h * 0.58 + 2), (w - 3, 5)], fill=(255, 250, 235, 150), width=1)
            d.line([(3, h - 4), (w * 0.36, h * 0.44)], fill=(150, 134, 108, 120), width=1)
            d.line([(w - 3, h - 4), (w * 0.64, h * 0.44)], fill=(150, 134, 108, 120), width=1)
            cx, cy = w / 2, h * 0.58
            blob = [(cx + (9.5 + rs.uniform(-2, 2.4)) * math.cos(a), cy + (9.5 + rs.uniform(-2, 2.4)) * math.sin(a)) for a in np.linspace(0, 6.283, 14, endpoint=False)]
            d.polygon([(x + 1.5, y + 2) for x, y in blob], fill=(60, 20, 14, 120))
            d.polygon(catmull(blob, 4, closed=True), fill=(170, 34, 30, 255), outline=(104, 16, 16, 255))
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=(120, 18, 18, 255), width=1)
            d.ellipse([cx - 4, cy - 5, cx, cy - 2], fill=(236, 120, 104, 200))
        else:                 # the front: a stamp, a postmark ring, three ruled lines of address
            d.rectangle([w - 26, 7, w - 8, 28], fill=(150, 60, 52, 255), outline=(240, 232, 214, 255))
            d.ellipse([w - 50, 6, w - 26, 30], outline=(40, 40, 50, 150), width=1)
            for q, ln in enumerate((46, 38, 30)):
                d.line([(16, 34 + q * 9), (16 + ln, 34 + q * 9 + rs.uniform(-1, 1))], fill=(50, 50, 70, 190), width=2)
        A[f"letter{k}"] = im


def build_pins():
    S = 4
    r = 9
    im = Image.new("RGBA", (40 * S, 40 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    c = 20 * S
    d.ellipse([c - r * S + 3 * S, c - r * S + 5 * S, c + r * S + 5 * S, c + r * S + 7 * S], fill=(20, 12, 4, 110))
    for q in range(r * S, 0, -1):
        f = q / (r * S)
        col = mix_color((236, 200, 110), (120, 84, 30), f ** 1.6)
        d.ellipse([c - q - (1 - f) * 2.2 * S, c - q - (1 - f) * 2.8 * S, c + q - (1 - f) * 2.2 * S, c + q - (1 - f) * 2.8 * S], fill=col + (255,))
    d.ellipse([c - 5 * S, c - 6 * S, c - 1 * S, c - 3 * S], fill=(255, 246, 210, 230))
    A["pin"] = im.resize((40, 40), Image.LANCZOS)
    # a brass paper fastener: flatter, with a slot shadow
    im = Image.new("RGBA", (40 * S, 40 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([c - 10 * S + 2 * S, c - 10 * S + 4 * S, c + 10 * S + 3 * S, c + 10 * S + 5 * S], fill=(20, 12, 4, 120))
    d.ellipse([c - 10 * S, c - 10 * S, c + 10 * S, c + 10 * S], fill=(190, 150, 70, 255), outline=(84, 58, 20, 255), width=S)
    d.ellipse([c - 8 * S, c - 9 * S, c + 5 * S, c + 3 * S], fill=(224, 188, 100, 255))
    d.line([(c - 5 * S, c + 1 * S), (c + 5 * S, c - 1 * S)], fill=(96, 68, 24, 255), width=S)
    A["brad"] = im.resize((40, 40), Image.LANCZOS)
    # hole-punch confetti: the bubbles
    for k in range(3):
        rr = (7, 10, 13)[k]
        b = Image.new("RGBA", (rr * 2 + 4, rr * 2 + 4), (0, 0, 0, 0))
        ImageDraw.Draw(b).ellipse([2, 2, rr * 2 + 1, rr * 2 + 1], fill=(226, 240, 236, 235), outline=(150, 190, 186, 255))
        A[f"dot{k}"] = bevel(b, 20, 40)


def metal(w, h, base=(170, 176, 180), seed=0, along=True):
    """Ground steel: a bright band, dark edges, fine grinding lines."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = yy / max(1, h - 1)
    band = 0.55 + 0.6 * np.exp(-((v - 0.32) / 0.2) ** 2) - 0.25 * (v > 0.8)
    lines = (vnoise((h, w), 2, seed, 1, sy=200 if not along else 2) - 0.5) if not along else (vnoise((h, w), 200, seed, 1, sy=1.5) - 0.5)
    a = np.ones((h, w, 3), np.float32) * np.array(base, np.float32) * (band + 0.18 * lines)[..., None]
    return a


def build_tools():
    # ---- scissors: two halves on one screw. Each half: blade toward +x, loop handle toward -x. Pivot at (300, 60).
    def half(flip):
        w, h = 620, 150
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        blade = [(300, 46), (590, 58), (604, 64), (300, 78)]
        bm = poly_mask((w, h), blade)
        bl = to_img(metal(w, h, (188, 194, 198), 3)).convert("RGBA")
        bl.putalpha(bm)
        im.alpha_composite(bl)
        d = ImageDraw.Draw(im, "RGBA")
        d.line([(304, 75), (598, 65)], fill=(246, 250, 252, 230), width=2)       # the ground edge
        d.line([(300, 47), (588, 58)], fill=(70, 76, 84, 200), width=2)
        # shank and loop, black japanned
        sh = [(300, 44), (300, 80), (170, 96), (120, 112), (120, 88), (170, 70)]
        d.polygon(sh, fill=(30, 28, 30, 255))
        d.line([(296, 48), (172, 74), (124, 92)], fill=(110, 108, 112, 255), width=3)
        d.ellipse([14, 66, 136, 146], fill=(30, 28, 30, 255))
        d.ellipse([34, 82, 116, 132], fill=(0, 0, 0, 0))
        d.arc([18, 70, 132, 142], 190, 300, fill=(120, 118, 122, 255), width=3)
        if flip:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        return im
    A["sc_a"], A["sc_b"] = half(False), half(True)
    # ---- pencil: yellow hexagonal, tip at (0, 14)
    w, h = 360, 28
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = yy / (h - 1)
    facet = np.where(v < 0.33, 1.12, np.where(v < 0.66, 0.96, 0.74))
    a = np.ones((h, w, 3), np.float32) * np.array([226, 172, 40], np.float32) * facet[..., None]
    a[:, :54] = np.array([222, 190, 150], np.float32) * (1.1 - 0.4 * v)[:, :54, None]                # the sharpened wood
    a[:, :16] = np.array([60, 60, 66], np.float32)                                                    # the lead
    a[:, 300:330] = np.array([190, 190, 196], np.float32) * (1.15 - 0.5 * v)[:, 300:330, None]         # ferrule
    a[:, 330:] = np.array([206, 110, 110], np.float32) * (1.1 - 0.4 * v)[:, 330:, None]               # rubber
    m = poly_mask((w, h), [(0, 14), (54, 1), (w - 1, 1), (w - 1, h - 1), (54, h - 1)])
    p = to_img(a).convert("RGBA")
    p.putalpha(m)
    A["pencil"] = p
    # ---- brush: tip at (0, 16)
    w, h = 400, 32
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = yy / (h - 1)
    a = np.ones((h, w, 3), np.float32) * np.array([150, 40, 34], np.float32) * (1.25 - 0.7 * v)[..., None]   # lacquered handle
    a[:, 70:128] = np.array([196, 198, 202], np.float32) * (1.2 - 0.6 * v)[:, 70:128, None]
    hair = vnoise((h, 70), 60, 4, 1, sy=1.6)
    a[:, :70] = np.array([34, 32, 40], np.float32) * (0.7 + 0.8 * hair)[..., None]
    m = poly_mask((w, h), [(0, 16), (30, 6), (70, 3), (128, 5), (w - 1, 9), (w - 1, 23), (128, 27), (70, 29), (30, 26)])
    b = to_img(a).convert("RGBA")
    b.putalpha(m)
    A["brush"] = b


def scissors_img(open_deg):
    """Both halves about the screw at (300, 60), opened by open_deg. Returns sprite and its pivot."""
    key = ("sc", round(open_deg))
    if key not in A:
        size = (700, 700)
        cv = Image.new("RGBA", size, (0, 0, 0, 0))
        for half, sgn in ((A["sc_b"], 1), (A["sc_a"], -1)):
            big = Image.new("RGBA", size, (0, 0, 0, 0))
            big.paste(half, (350 - 300, 350 - (60 if sgn < 0 else 90)))
            cv.alpha_composite(big.rotate(sgn * round(open_deg) / 2, center=(350, 350), resample=Image.BICUBIC))
        d = ImageDraw.Draw(cv, "RGBA")
        d.ellipse([341, 341, 359, 359], fill=(200, 204, 208, 255), outline=(40, 40, 46, 255))
        d.line([(345, 350), (355, 350)], fill=(40, 40, 46, 255), width=2)
        A[key] = cv
    return A[key], (350, 350)


# ---- the green gel: the reservoir -------------------------------------------

GEL_BOX = (52, 50, 1874, 1040)


def build_gel():
    h, w = WH, WW
    x0, y0, x1, y1 = GEL_BOX
    m = poly_mask((w, h), wobbly([(x0, y0), (x1, y0 + 4), (x1 - 3, y1), (x0 + 2, y1 - 3)], 2.0, 14))
    A["gel_mask"] = np.asarray(m, np.float32) / 255
    mott = vnoise((h, w), 260, 15, 3)
    tint = np.array([0.24, 0.60, 0.56], np.float32)[None, None] * (0.86 + 0.28 * mott)[..., None]
    A["gel_tint"] = tint.astype(np.float32)

    def creases(seed, base_deg, n):
        """Folds in a sheet of acetate run nearly straight, right across it."""
        rs = np.random.RandomState(seed)
        im = Image.new("L", (w // 2, h // 2), 0)
        d = ImageDraw.Draw(im)
        for _ in range(n):
            ang = math.radians(base_deg + rs.uniform(-9, 9))
            cx, cy = rs.uniform(0, w / 2), rs.uniform(0, h / 2)
            ln = rs.uniform(500, 1400) / 2
            bend = rs.uniform(-0.12, 0.12)
            pts = []
            for q in range(13):
                u = q / 12 - 0.5
                aa = ang + bend * u
                pts.append((cx + ln * u * math.cos(aa), cy + ln * u * math.sin(aa) + 14 * math.sin(u * 7 + cx)))
            d.line(pts, fill=int(rs.uniform(120, 255)), width=int(rs.uniform(1, 3)))
        return (np.asarray(im.filter(ImageFilter.GaussianBlur(1.6)).resize((w, h), Image.BILINEAR), np.float32) / 255).astype(np.float32)
    A["gel_w"] = [creases(16, 18, 9), creases(17, -32, 8), creases(18, 74, 7)]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    A["gel_sheen"] = (np.exp(-(((xx / w + yy / h) - 0.55) / 0.16) ** 2) * 0.10).astype(np.float32)
    A["yy"] = yy


def apply_gel(a, t, front=None, glint=1.0):
    """Lay the gel over the table (a: float RGB array, in place). front: how far down it has been pulled.
    The sheet is never quite still: its creases catch the lamp differently as it breathes."""
    m = A["gel_mask"]
    if front is not None:
        m = m * np.clip((front - A["yy"]) / 6.0, 0, 1)
    w1, w2, w3 = A["gel_w"]
    k1 = 0.5 + 0.5 * math.sin(t * 0.9)
    k2 = 0.5 + 0.5 * math.sin(t * 0.63 + 2.0)
    k3 = 0.5 + 0.5 * math.sin(t * 1.21 + 4.0)
    hi = (w1 * k1 + w2 * k2 + w3 * k3) * 0.55 + A["gel_sheen"]
    mm = m[..., None]
    tinted = (a / 255.0) ** 1.12 * 255.0 * A["gel_tint"] + np.array([0, 8, 9], np.float32)
    tinted += (hi * 120 * glint)[..., None] * np.array([0.8, 1.0, 0.96], np.float32)
    a *= (1 - mm)
    a += tinted * mm
    if front is not None and front < WH + 60:           # the leading edge, held up off the table as it is drawn across
        band = np.exp(-((A["yy"] - front + 14) / 12.0) ** 2) * A["gel_mask"]
        a += (band * 90)[..., None]
        shade = np.clip(1 - (A["yy"] - front) / 46.0, 0, 1) * (A["yy"] > front) * A["gel_mask"]
        a *= (1 - 0.42 * shade)[..., None]
    return a


# ---- brass, tin, glass ---------------------------------------------------------

def brass_ring(r_in, r_out, bolts=6, seed=0, start=-90.0):
    """A turned brass ring with a bevelled inner lip and six hexagon bolts, lit from the upper left."""
    R = int(r_out + 8)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    r = np.hypot(xx, yy) + 1e-6
    th = np.arctan2(yy, xx)
    wd = r_out - r_in
    f = (r - r_in) / wd
    prof = np.where(f < 0.2, f / 0.2, np.where(f < 0.84, 1.0, np.sqrt(np.clip(1 - ((f - 0.84) / 0.16) ** 2, 0, 1))))
    slope = (np.gradient(prof, axis=1) * xx + np.gradient(prof, axis=0) * yy) / r * wd
    lit = 0.66 - 0.5 * slope * (np.cos(th) * -0.62 + np.sin(th) * -0.78)
    rs = np.random.RandomState(seed)
    lathe = np.interp(r, np.arange(0, R * 1.5), rs.uniform(-1, 1, int(R * 1.5))) * 0.05
    tarn = (vnoise(r.shape, 46, seed + 1, 3) - 0.5) * 0.24
    conic = 0.07 * np.cos(2 * (th - 0.9))                 # the lamp streak a turned ring always shows
    col = np.array([196, 154, 68], np.float32)[None, None] * (lit + lathe + tarn + conic)[..., None]
    col[..., 2] *= 0.86
    al = np.clip(np.minimum(r - r_in, r_out - r) + 0.5, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([R - r_in - 1, R - r_in - 1, R + r_in + 1, R + r_in + 1], outline=(36, 24, 10, 210), width=max(1, int(wd * 0.06)))
    d.ellipse([R - r_out, R - r_out, R + r_out, R + r_out], outline=(46, 32, 12, 190), width=max(1, int(wd * 0.03)))
    br = wd * 0.19
    rm = r_in + wd * 0.56
    for b in range(bolts):
        a = math.radians(start + 360 * b / bolts)
        cx, cy = R + rm * math.cos(a), R + rm * math.sin(a)
        rot = rs.uniform(0, 1.0)
        hexa = [(cx + br * math.cos(rot + q * math.pi / 3), cy + br * math.sin(rot + q * math.pi / 3)) for q in range(6)]
        d.polygon([(x + br * 0.2, y + br * 0.3) for x, y in hexa], fill=(36, 22, 8, 160))
        d.polygon(hexa, fill=(164, 124, 50, 255), outline=(58, 40, 14, 255))
        for q in range(6):
            p0, p1 = hexa[q], hexa[(q + 1) % 6]
            l_ = (((p0[0] + p1[0]) / 2 - cx) * -0.62 + ((p0[1] + p1[1]) / 2 - cy) * -0.78) / br
            c = tuple(int(np.clip(v * (0.8 + 0.5 * l_), 0, 255)) for v in (198, 156, 72))
            d.polygon([p0, p1, (cx + (p1[0] - cx) * 0.6, cy + (p1[1] - cy) * 0.6), (cx + (p0[0] - cx) * 0.6, cy + (p0[1] - cy) * 0.6)], fill=c + (255,))
        d.ellipse([cx - br * 0.58, cy - br * 0.58, cx + br * 0.58, cy + br * 0.58], fill=(208, 168, 84, 255), outline=(70, 50, 20, 230))
        d.line([(cx - br * 0.3, cy - br * 0.36), (cx + br * 0.1, cy - br * 0.46)], fill=(252, 236, 176, 230), width=max(1, int(br * 0.14)))
    return img


def tinplate(w, h, seed, base=(150, 164, 168), ribs=0, rust=0.45):
    brush = vnoise((h, w), 110, seed, 2, sy=5) - 0.5
    blot = vnoise((h, w), 70, seed + 1, 3)
    a = np.ones((h, w, 3), np.float32) * np.array(base, np.float32) * (1 + brush * 0.18)[..., None]
    if ribs:
        xx = np.arange(w, dtype=np.float32)[None, :]
        a *= (1 + 0.12 * np.sin(xx / ribs * 2 * math.pi))[..., None]
    r = np.clip((blot - (0.8 - rust * 0.3)) * 6, 0, 1)[..., None]
    return a * (1 - r) + np.array([126, 76, 44], np.float32) * (0.8 + 0.4 * vnoise((h, w), 6, seed + 2)[..., None]) * r


TIN_W, TIN_H, TIN_PAD = 620, 290, 110
TIN_PORT = (TIN_PAD + 190, TIN_PAD + 150)          # porthole centre in the sprite; the nose is at the left
TIN_NOZZLE = (TIN_PAD - 62, TIN_PAD + 28)          # the mouth of the intake pipe
TIN_LAMP = (TIN_PAD - 14, TIN_PAD + 232)


def build_tin():
    """Turkey's submersible: a bread-roll tin on its side, nose to the left, one six-bolt brass porthole."""
    w, h, pad = TIN_W, TIN_H, TIN_PAD
    Wd, Hd = w + 2 * pad, h + 2 * pad
    a = tinplate(Wd, Hd, 5, ribs=22, rust=0.4)
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    v = np.clip((yy - pad) / h, 0, 1)
    a *= (0.42 + 0.82 * np.exp(-((v - 0.26) / 0.2) ** 2) + 0.22 * np.exp(-((v - 0.96) / 0.07) ** 2))[..., None]     # a drum: bright shoulder, dark belly
    rs = np.random.RandomState(8)
    for _ in range(22):                                   # rust running down from the seams
        x0, y0, ln, wd = pad + rs.uniform(10, w - 10), pad + rs.uniform(10, 130), rs.uniform(50, 170), rs.uniform(3, 9)
        st = np.exp(-((xx - x0) / wd) ** 2) * np.clip((yy - y0) / ln, 0, 1) * np.clip(1 - (yy - y0) / ln, 0, 1) * 2.4
        a = a * (1 - 0.5 * st[..., None]) + np.array([112, 64, 36], np.float32) * 0.5 * st[..., None]
    img = to_img(a).convert("RGBA")
    m = Image.new("L", (Wd, Hd), 0)
    md = ImageDraw.Draw(m)
    md.rounded_rectangle([pad, pad, pad + w, pad + h], radius=18, fill=255)
    rims = [(pad - 3, 20), (pad + w - 17, 20)]
    for x, wd in rims:
        md.rounded_rectangle([x, pad - 10, x + wd, pad + h + 10], radius=8, fill=255)
    img.putalpha(m)
    d = ImageDraw.Draw(img, "RGBA")
    for x, wd in rims + [(pad + w - 130, 10)]:
        top, bot = (pad - 10, pad + h + 10) if wd > 12 else (pad + 3, pad + h - 3)
        for q in range(int(wd)):
            f = q / wd
            l_ = 0.5 + 0.75 * math.sin(f * math.pi) ** 2 * (1.25 - f)
            d.line([(x + q, top + 4), (x + q, bot - 4)], fill=tuple(int(min(255, c * l_)) for c in (176, 192, 196)) + (255,))
        d.line([(x + wd, top + 9), (x + wd, bot - 9)], fill=(22, 30, 36, 190), width=2)
    for k in range(9):
        y = pad + 22 + k * (h - 44) / 8
        for x in (pad + 34, pad + w - 32, pad + w - 148):
            d.ellipse([x - 6, y - 4, x + 8, y + 8], fill=(30, 40, 46, 150))
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(98, 112, 118, 255))
            d.ellipse([x - 5, y - 6, x + 1, y], fill=(222, 230, 228, 255))
    d.line([(pad + 30, pad + 196), (pad + w - 150, pad + 196)], fill=(30, 40, 46, 150), width=2)       # the soldered seam
    d.line([(pad + 30, pad + 193), (pad + w - 150, pad + 193)], fill=(226, 232, 230, 60), width=2)
    # the paper label, pasted on a little crooked
    lab = to_img(paper_tex(196, 92, (230, 216, 184), 9, grain=0.04, mottle=0.1)).convert("RGBA")
    ld = ImageDraw.Draw(lab)
    ld.rectangle([6, 6, 189, 85], outline=(124, 44, 40, 255), width=2)
    ld.text((98, 38), "ROLLS", font=font("serif", 46), fill=(124, 44, 40, 255), anchor="mm")
    ld.text((98, 71), "ONE DOZEN · TROUT TOWN", font=font("mono", 10), fill=(90, 60, 50, 255), anchor="mm")
    lab = lab.rotate(3, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(shadow_of(lab, 3, 0.45), (pad + 318, pad + 46))
    img.alpha_composite(lab, (pad + 314, pad + 40))
    img.putalpha(ImageChops.darker(img.getchannel("A"), m))
    d = ImageDraw.Draw(img, "RGBA")
    brass, bdark, bline = (176, 138, 60, 255), (128, 96, 40, 255), (56, 38, 14, 255)
    for x0 in (150, 360):                                 # lead keel
        d.rounded_rectangle([pad + x0, pad + h - 3, pad + x0 + 140, pad + h + 26], radius=8, fill=(66, 74, 80, 255), outline=(26, 30, 34, 255), width=2)
        d.line([(pad + x0 + 9, pad + h + 4), (pad + x0 + 130, pad + h + 4)], fill=(128, 138, 142, 255), width=2)
    d.rounded_rectangle([pad + 300, pad - 23, pad + 430, pad + 4], radius=6, fill=(150, 166, 172, 255), outline=(30, 40, 46, 255), width=2)   # hatch: a jar lid
    d.line([(pad + 306, pad - 15), (pad + 424, pad - 15)], fill=(232, 238, 236, 255), width=2)
    d.arc([pad + 330, pad - 52, pad + 400, pad + 2], 180, 360, fill=(60, 66, 70, 255), width=4)
    # the intake: a bent tin pipe over the nose, ending in a flattened funnel. A hose? A letter slot?
    nx, ny = TIN_NOZZLE
    pipe = [(pad + 96, pad + 4), (pad + 96, pad - 44), (pad + 40, pad - 60), (pad - 20, pad - 30), (nx + 34, ny - 6)]
    d.line(pipe, fill=(52, 64, 70, 255), width=26, joint="curve")
    d.line([(x - 3, y - 5) for x, y in pipe], fill=(150, 166, 170, 255), width=11, joint="curve")
    d.line([(x - 4, y - 8) for x, y in pipe], fill=(222, 230, 230, 255), width=3, joint="curve")
    fun = [(nx + 44, ny - 26), (nx - 6, ny - 44), (nx - 14, ny + 34), (nx + 36, ny + 12)]
    d.polygon(fun, fill=brass, outline=bline)
    d.polygon([fun[1], fun[2], (nx - 4, ny + 26), (nx + 4, ny - 34)], fill=(40, 28, 16, 255))          # the dark of the slot
    d.line([fun[0], fun[1]], fill=(240, 210, 130, 255), width=3)
    d.ellipse([pad + 82, pad - 6, pad + 110, pad + 12], fill=brass, outline=bline)
    # rudder, shaft, lamp
    d.polygon([(pad + w - 6, pad + 34), (pad + w + 66, pad - 24), (pad + w + 76, pad + 92), (pad + w - 3, pad + 106)], fill=(124, 140, 146, 255), outline=(30, 40, 46, 255))
    d.line([(pad + w + 10, pad + 42), (pad + w + 62, pad - 4)], fill=(214, 224, 224, 200), width=2)
    d.rectangle([pad + w - 3, pad + h / 2 + 34, pad + w + 46, pad + h / 2 + 52], fill=bdark, outline=bline)
    d.ellipse([pad + w + 34, pad + h / 2 + 24, pad + w + 70, pad + h / 2 + 60], fill=brass, outline=bline)
    lx, ly = TIN_LAMP
    d.line([(pad + 8, ly + 16), (lx + 22, ly + 10)], fill=(50, 58, 62, 255), width=9)
    body = [(lx + 46, ly - 10), (lx - 6, ly - 40), (lx - 30, ly + 3), (lx + 24, ly + 34)]
    d.polygon(body, fill=brass, outline=bline)
    d.polygon([body[0], body[1], (lx + 3, ly - 28), (lx + 42, ly - 2)], fill=(226, 190, 104, 255))
    d.polygon([(lx - 6, ly - 40), (lx - 30, ly + 3), (lx - 20, ly + 8), (lx + 4, ly - 34)], fill=(255, 236, 170, 255), outline=bline)
    A["tin"] = img
    A["ring_small"] = brass_ring(64, 92, 6, seed=3)
    b = Image.new("RGBA", (46, 170), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.ellipse([4, 3, 42, 84], fill=brass, outline=bline)
    bd.ellipse([12, 9, 28, 62], fill=(214, 178, 96, 255))
    bd.ellipse([4, 86, 42, 167], fill=bdark, outline=bline)
    A["prop"] = b
    r = 66
    yy, xx = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    gl = np.exp(-(((xx - r * 1.2) / (r * 0.9)) ** 2 + ((yy - r * 0.2) / (r * 0.8)) ** 2))
    bg = np.array([40, 24, 14], np.float32)[None, None] * (1 - gl[..., None]) + np.array([232, 150, 60], np.float32)[None, None] * gl[..., None]
    A["win_bg"] = to_img(bg).convert("RGBA")


def tin_sprite(t, duck=0.0, wattle=0.0):
    img = A["tin"].copy()
    px, py = TIN_PORT
    r = 66
    win = A["win_bg"].copy()
    tk = turkey_img(wattle, 230).transpose(Image.FLIP_LEFT_RIGHT)          # he looks out toward the nose
    win.alpha_composite(tk, (int(r - tk.width * 0.58), int(r * 0.95 - tk.height * 0.27 + duck)))
    ImageDraw.Draw(win, "RGBA").ellipse([-r * 0.3, -r * 0.7, r * 1.2, r * 0.55], fill=(210, 240, 235, 34))
    msk = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(msk).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    img.paste(win, (int(px - r), int(py - r)), msk)
    rg = A["ring_small"]
    img.alpha_composite(rg, (int(px - rg.width / 2), int(py - rg.height / 2)))
    bl = A["prop"]
    sq = abs(math.cos(t * 5.0)) * 0.85 + 0.15
    b2 = bl.resize((bl.width, max(2, int(bl.height * sq))), Image.BILINEAR)
    img.alpha_composite(b2, (int(TIN_PAD + TIN_W + 46), int(TIN_PAD + TIN_H / 2 + 42 - b2.height / 2)))
    return img.resize((int(img.width * TS), int(img.height * TS)), Image.BICUBIC)


def flex(spr, phase, amp=9.0):
    """Bend a fish along its length: the tail swings, the head hardly moves (head at left)."""
    a = np.asarray(spr)
    h, w = a.shape[:2]
    x = np.arange(w) / w
    dy = (amp * (x ** 1.8) * np.sin(phase - 2.6 * x)).astype(np.int32)
    yy = np.arange(h)[:, None] - dy[None, :]
    ok = (yy >= 0) & (yy < h)
    out = a[np.clip(yy, 0, h - 1), np.arange(w)[None, :]]
    out[~ok] = 0
    return Image.fromarray(out, "RGBA")


# ---- the sack ---------------------------------------------------------------------

def build_sack():
    """The canvas mail sack. If the 1937 photograph is here it is cut out of that; the open end is at the right."""
    A["sack"] = None
    p = SRC / "sack.jpg"
    if p.exists():
        im = Image.open(p).convert("RGB")
        A["sack"], A["sack_pivot"] = sack_from_photo(im)
        A["post"] = post_from_photo(im)
        return
    w, h = 250, 150                                   # stand-in while the archive is slow: plain cut canvas-coloured paper
    pts = [(10, 70), (30, 30), (90, 14), (170, 20), (236, 8), (228, 60), (240, 136), (176, 122), (96, 138), (34, 118)]
    tex = paper_tex(w, h, (168, 146, 110), 70, grain=0.1, fibre=0.08, mottle=0.14)
    A["sack"] = cut_paper(tex, poly_mask((w, h), catmull(pts, 6, closed=True)))
    A["sack_pivot"] = (26, 74)
    A["sack_foraged"] = False


SACK_CUT = [(427, 404), (398, 424), (380, 436), (364, 466), (354, 540), (356, 620), (362, 700), (370, 748), (420, 755), (482, 748),
            (519, 724), (520, 690), (508, 620), (490, 540), (472, 470), (456, 432), (440, 410)]
POST_CUT = [(230, 120), (279, 118), (281, 300), (268, 520), (254, 700), (249, 856), (205, 856), (212, 600), (220, 300)]


def sack_from_photo(im):
    """Scissor the sack out of Lee's photograph along a traced line (measured on the 785 px scan)."""
    k = im.width / 785.0
    x0, y0, x1, y1 = 340, 392, 532, 768
    m = poly_mask(im.size, [(x * k, y * k) for x, y in catmull(SACK_CUT, 5, closed=True)])
    g = np.asarray(im.convert("L"), np.float32)
    rgb = (g[..., None] * np.array([1.0, 0.975, 0.92], np.float32))
    o = to_img(rgb).convert("RGBA")
    o.putalpha(m)
    o = o.crop(tuple(int(v * k) for v in (x0, y0, x1, y1)))
    sc = 300.0 / o.height
    o = bevel(o.resize((int(o.width * sc), 300), Image.LANCZOS), 26, 40)
    return o, ((427 - x0) * k * sc, (408 - y0) * k * sc)


def post_from_photo(im):
    k = im.width / 785.0
    x0, y0, x1, y1 = 198, 112, 288, 862
    m = poly_mask(im.size, [(x * k, y * k) for x, y in wobbly(POST_CUT, 0.6, 3)])
    g = np.asarray(im.convert("L"), np.float32)
    o = to_img(g[..., None] * np.array([1.0, 0.975, 0.92], np.float32)).convert("RGBA")
    o.putalpha(m)
    o = o.crop(tuple(int(v * k) for v in (x0, y0, x1, y1)))
    sc = 640.0 / o.height
    return bevel(o.resize((int(o.width * sc), 640), Image.BICUBIC), 22, 40)


# ---- the porthole, from inside the tin -------------------------------------------

PC = (566, 262)
RG = 206
RO = 250
VIEW_C = (950, 600)        # critic: pulled back and left so the whole of box #44 and its flag sit inside the rim
VIEW_S = 0.40


def build_port():
    a = tinplate(W, H, 31, base=(52, 62, 66), ribs=0, rust=-1.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a *= (0.55 + 0.25 * vnoise((H, W), 200, 32, 2))[..., None]
    glow = np.exp(-(((xx - 130) / 330) ** 2 + ((yy - 560) / 260) ** 2))           # Turkey's lamp, low on the left
    a = a * (0.7 + 0.5 * glow[..., None]) + np.array([90, 52, 18], np.float32) * glow[..., None] * 0.5
    wall = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(wall, "RGBA")
    for x in (78, 868):                                # frame ribs of the tin, riveted
        d.rectangle([x, 0, x + 22, H], fill=(30, 38, 42, 255))
        d.line([(x + 2, 0), (x + 2, H)], fill=(96, 110, 114, 255), width=2)
        d.line([(x + 23, 0), (x + 23, H)], fill=(8, 10, 12, 200), width=3)
        for y in range(24, H, 62):
            d.ellipse([x + 5, y, x + 17, y + 12], fill=(74, 88, 92, 255), outline=(14, 18, 20, 255))
            d.ellipse([x + 6, y + 1, x + 11, y + 6], fill=(150, 166, 168, 255))
    # the shadow the ring throws on the wall
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).ellipse([PC[0] - RO - 4 + 10, PC[1] - RO - 4 + 14, PC[0] + RO + 4 + 10, PC[1] + RO + 4 + 14], fill=190)
    wall.paste((6, 8, 10, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(wall, "RGBA")
    # hinge at the left, dog latch at the right (drawn under the ring's edge)
    hx, hy = PC[0] - RO - 26, PC[1]
    d.rounded_rectangle([hx - 22, hy - 62, hx + 46, hy + 62], radius=5, fill=(36, 38, 40, 255), outline=(8, 8, 10, 255), width=2)
    d.rectangle([hx - 6, hy - 70, hx + 8, hy + 70], fill=(70, 74, 78, 255), outline=(8, 8, 10, 255))
    d.line([(hx - 3, hy - 68), (hx - 3, hy + 68)], fill=(150, 156, 160, 255), width=2)
    for yy_ in (-44, 44):
        for xx_ in (-13, 30):
            d.ellipse([hx + xx_ - 5, hy + yy_ - 5, hx + xx_ + 5, hy + yy_ + 5], fill=(100, 106, 110, 255), outline=(8, 8, 10, 255))
    lx, ly = PC[0] + RO - 6, PC[1]
    d.rounded_rectangle([lx, ly - 15, lx + 62, ly + 15], radius=6, fill=(176, 138, 60, 255), outline=(56, 38, 14, 255), width=2)
    d.line([(lx + 4, ly - 9), (lx + 56, ly - 9)], fill=(240, 210, 130, 255), width=2)
    d.ellipse([lx + 34, ly - 22, lx + 78, ly + 22], fill=(190, 150, 70, 255), outline=(56, 38, 14, 255), width=2)
    d.ellipse([lx + 46, ly - 10, lx + 66, ly + 10], fill=(120, 90, 36, 255), outline=(56, 38, 14, 255))
    # two things on the wall, one for each of Turkey's readings: an order board with nothing on it,
    # and a line with one sock pegged up to dry. Both cut paper.
    bw, bh = 118, 150
    board = cut_paper(paper_tex(bw, bh, (120, 84, 50), 61, grain=0.06, fibre=0.1, mottle=0.1), poly_mask((bw, bh), wobbly([(2, 2), (bw - 2, 3), (bw - 3, bh - 2), (3, bh - 3)], 1, 61)))
    sheet = cut_paper(paper_tex(96, 112, (226, 216, 190), 62, grain=0.03), poly_mask((96, 112), wobbly([(2, 2), (94, 3), (93, 78), (70, 110), (3, 109)], 1, 62)))
    sd = ImageDraw.Draw(sheet, "RGBA")
    sd.text((48, 14), "MISSION", font=font("mono", 13), fill=(40, 36, 40, 235), anchor="mm")
    sd.text((48, 29), "ORDERS", font=font("mono", 13), fill=(40, 36, 40, 235), anchor="mm")
    for q in range(5):
        sd.line([(12, 46 + q * 12), (84 - (q == 4) * 30, 46 + q * 12)], fill=(120, 110, 96, 150), width=1)
    board.alpha_composite(shadow_of(sheet, 2, 0.5), (13, 31))
    board.alpha_composite(sheet, (11, 28))
    bd = ImageDraw.Draw(board, "RGBA")
    bd.rounded_rectangle([34, 6, 84, 34], radius=4, fill=(176, 138, 60, 255), outline=(56, 38, 14, 255), width=2)
    bd.line([(38, 12), (80, 12)], fill=(244, 216, 140, 255), width=2)
    bd.ellipse([54, 0, 64, 10], fill=(60, 60, 64, 255))
    board = board.rotate(-4, expand=True, resample=Image.BICUBIC)
    wall.alpha_composite(shadow_of(board, 6, 0.7, (0, 0, 0)), (806 + 8, 360 + 10))
    wall.alpha_composite(board, (806, 360))
    d = ImageDraw.Draw(wall, "RGBA")
    d.line([(756, 40), (800, 58), (850, 66), (900, 62), (960, 44)], fill=(196, 180, 150, 255), width=2)          # the line
    sock = [(0, 0), (30, 0), (31, 58), (52, 72), (58, 90), (44, 100), (16, 96), (2, 78)]
    sk = cut_paper(paper_tex(62, 104, (232, 228, 216), 63, grain=0.06, fibre=0.06), poly_mask((62, 104), catmull(sock, 5, closed=True)))
    kd = ImageDraw.Draw(sk, "RGBA")
    kd.line([(1, 10), (30, 10)], fill=(168, 44, 40, 230), width=4)
    kd.line([(1, 18), (30, 18)], fill=(168, 44, 40, 230), width=2)
    kd.pieslice([36, 72, 62, 104], 300, 120, fill=(170, 166, 160, 255))
    sk.putalpha(ImageChops.multiply(sk.getchannel("A"), poly_mask((62, 104), catmull(sock, 5, closed=True))))
    sk = sk.rotate(-5, expand=True, resample=Image.BICUBIC)
    wall.alpha_composite(shadow_of(sk, 6, 0.7, (0, 0, 0)), (862 + 9, 62 + 9))
    wall.alpha_composite(sk, (862, 62))
    d = ImageDraw.Draw(wall, "RGBA")
    d.rectangle([872, 54, 880, 78], fill=(206, 170, 110, 255), outline=(70, 50, 24, 255))                           # the peg
    a_ = np.asarray(wall.convert("RGB"), np.float32)
    fall = np.clip(1.0 - np.hypot((xx - 760) / 900, (yy - 300) / 700) * 0.55, 0.45, 1.0)                           # these sit in the dim of the cabin
    a_[:, 740:] *= fall[:, 740:, None] * 0.8
    wall = to_img(a_).convert("RGBA")
    A["wall"] = wall
    A["ring_big"] = brass_ring(RG, RO, 6, seed=1, start=-90)
    # the glass: a thick pane. Dark toward its edge, one window-light, a faint arc opposite.
    S = 2 * RG
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - RG, yy - RG) / RG
    edge = np.clip((r - 0.78) / 0.22, 0, 1) ** 2
    A["glass_dark"] = (1 - 0.5 * edge)[..., None]
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g, "RGBA")
    gd.pieslice([14, 14, S - 14, S - 14], 198, 250, fill=(230, 250, 244, 46))
    gd.ellipse([40, 44, S - 2, S + 6], fill=(0, 0, 0, 0))
    gd.arc([10, 10, S - 10, S - 10], 30, 75, fill=(220, 246, 240, 70), width=5)
    A["glass_hi"] = g.filter(ImageFilter.GaussianBlur(5))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([0, 0, S - 1, S - 1], fill=255)
    A["glass_mask"] = m


# ================================================================ the staging ===

BOX = (706, 430)
BOX_R = -5.0
WORK = (1250, 606)
WORK_R = 2.0


def rot_pt(dx, dy, deg):
    r = math.radians(deg)
    return dx * math.cos(r) + dy * math.sin(r), -dx * math.sin(r) + dy * math.cos(r)


def sheet_pt(sx, sy, at=BOX, deg=BOX_R):
    dx, dy = rot_pt(sx - SHEET[0] / 2, sy - SHEET[1] / 2, deg)
    return at[0] + dx, at[1] + dy


HINGE = sheet_pt(472, 268)
MOUTH = sheet_pt(472, 162)
FLAGP = sheet_pt(112, 100)
SACKP = sheet_pt(480, 236)
SACK_R = 31.0
_pt = sheet_pt(258, 210)
POST = (_pt[0] - 48, _pt[1] + 300)

# Part one, in order of laying down. (key, t0, t1, from, to, rot). z order is this order.
LAID = [
    ("print_road", 0.3, 1.2, (-560, 560), (560, 440), -2.0),
    ("print_po", 0.9, 1.7, (1150, 1500), (1270, 880), 4.0),
    ("print_mailbox", 1.4, 2.2, (1380, -330), (1290, 250), 3.0),
    ("print_cross", 1.9, 2.7, (2400, 860), (1686, 760), -3.5),
    ("print_sackprint", 2.4, 3.1, (2300, 200), (1716, 262), 5.0),
    ("post", 2.9, 3.5, (480, 1500), POST, -9.0),
    ("body", 8.5, 9.3, WORK, BOX, BOX_R),
    ("mouth", 9.0, 9.6, (1500, -160), MOUTH, BOX_R),
    ("strip_box", 10.0, 10.5, (300, 1300), (716, 600), -3.0),
]
N_STATIC = len(LAID)
T_DOOR, T_FLAG, T_SACK = (9.4, 9.9), (12.3, 12.8), (11.95, 12.55)
T_SHEET = (3.3, 4.0)
T_DRAW = (4.2, 5.1)
T_CUT = (5.4, 6.9)
T_WASTE = (6.95, 7.6)
T_INK = (7.3, 8.4)
T_GEL = (10.6, 11.9)
PINS = [   # (time it goes in, x, y, kind)
    (1.25, 330, 130, "pin"), (1.4, 800, 122, "pin"), (1.78, 1270, 740, "pin"), (2.28, 1296, 96, "pin"),
    (2.78, 1686, 560, "pin"), (3.18, 1716, 76, "pin"), (3.56, POST[0] + 44, POST[1] + 270, "pin"),
    (9.36, sheet_pt(120, 100)[0], sheet_pt(120, 100)[1], "pin"), (9.5, sheet_pt(250, 242)[0], sheet_pt(250, 242)[1], "pin"),
    (9.98, HINGE[0], HINGE[1], "brad"), (10.55, 640, 600, "pin"),
]
GEL_PINS = [(11.95, 70, 66), (12.05, 1856, 70), (12.15, 66, 1022), (12.25, 1858, 1026), (12.62, SACKP[0], SACKP[1])]
LETTERS = [   # (key, x, y, rot, dealt at)
    ("letter0", 1070, 820, -20.0, 12.5), ("letter1", 1128, 894, 24.0, 12.64), ("letter2", 1172, 772, -35.0, 12.78),
    ("letter3", 1028, 916, 50.0, 12.92), ("letter4", 1216, 852, -8.0, 13.06),
]
TROUT_A = (1352, 848)


def with_strip(print_key, strip_key, dx=0.0):
    pr, st = A[print_key], A[strip_key]
    w, h = max(pr.width, st.width), pr.height + st.height - 12
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(pr, ((w - pr.width) // 2, 0))
    sx = int((w - st.width) / 2 + dx)
    im.alpha_composite(shadow_of(st, 2, 0.5), (sx + 2, pr.height - 20 + 3))
    im.alpha_composite(st.rotate(0, expand=False), (sx, pr.height - 20))
    return im


def build_stage():
    for key, fn, pw, lines in PRINTS:
        A["print_" + key] = with_strip("print_" + key, "strip_" + key)
    A["static"] = {}


def piece_img(key):
    if key == "body":
        return body_img(len(STROKES), 0.0)
    return A[key]


def flight(t, t0, t1, src_, dst, rot, lift0=22.0):
    """A piece handed in from the edge of the frame: carried high, set down, a small settle."""
    f = ease(t, t0, t1)
    x, y = lerp2(src_, dst, f)
    lift = 1.0 + lift0 * (1 - f) ** 0.7
    r = rot + 7.0 * (1 - f) + spring(t, t1, 1.4, 5.0, 9.0)
    return x, y, r, lift


def static_layer(t):
    """Everything already lying still under the gel, baked. Pieces settle in the order they were laid."""
    n = 0
    for key, t0, t1, s_, d_, r_ in LAID:
        if t >= t1 + 0.45:
            n += 1
        else:
            break
    ck = n
    if ck not in A["static"]:
        cv = A["board"].copy()
        for key, t0, t1, s_, d_, r_ in LAID[:n]:
            lay(cv, piece_img(key), d_[0], d_[1], r_, 1.0)
        if len(A["static"]) > 4:
            A["static"].pop(next(iter(A["static"])))
        A["static"][ck] = cv
    return A["static"][ck].copy(), n


def draw_pin(cv, t, tp, x, y, kind):
    f = ramp(t, tp, tp + 0.12)
    if f <= 0:
        return
    lay(cv, A[kind], x - 14 * (1 - f), y - 22 * (1 - f), shadow=False, scale=1.0 + 0.5 * (1 - f))


def door_state(t):
    """The door hangs open on its brass fastener. It swings when let go, and again whenever the sack lurches."""
    sw = spring(t, T_DOOR[1], 16.0, 1.7, 2.6)
    for tk, amp in KICKS:
        sw += spring(t, tk, amp * 0.6, 1.7, 2.4)
    return BOX_R - 101.0 + sw


def sack_state(t):
    sw = spring(t, T_SACK[1], 9.0, 0.9, 1.4)
    for tk, amp in KICKS:
        sw += spring(t, tk, amp, 0.9, 1.1)
    return SACK_R + sw


KICKS = [(T1 + 3.2, 8.0), (T1 + 7.3, 5.0), (T2 + 2.7, 6.0), (T2 + 5.9, 5.0)]
T_FLAG_UP = T2 + 2.75


def flag_state(t):
    if t < T_FLAG_UP:
        return BOX_R + 88.0 + spring(t, T_FLAG[1], 8.0, 2.4, 4.0)
    f = ease(t, T_FLAG_UP, T_FLAG_UP + 0.35)
    return BOX_R + 88.0 * (1 - f) + spring(t, T_FLAG_UP + 0.35, -11.0, 2.6, 3.2)


def under_gel(t):
    """The table up to (not including) the gel, as an RGBA canvas."""
    cv, n = static_layer(t)
    for key, t0, t1, s_, d_, r_ in LAID[n:]:
        if key == "body" or t < t0:
            continue
        x, y, r, lift = flight(t, t0, t1, s_, d_, r_)
        lay(cv, piece_img(key), x, y, r, lift)
    # the blue sheet, the work done on it, and the box body carried to its post
    if T_SHEET[0] <= t < T_WASTE[0]:
        x, y, r, lift = flight(t, T_SHEET[0], T_SHEET[1], (2300, 700), WORK, WORK_R)
        lay(cv, sheet_img(ramp(t, *T_DRAW), ramp(t, *T_CUT)), x, y, r, lift)
    if t >= T_WASTE[0]:
        if t < T_WASTE[1] + 0.2:
            f = ease(t, T_WASTE[0] + 0.1, T_WASTE[1])
            x, y = lerp2(WORK, (2460, 520), f)
            lay(cv, A["waste"], x, y, WORK_R - 20 * f, 1 + 20 * math.sin(math.pi * clamp(f * 1.2)))
        if t < LAID[6][2] + 0.45:
            nd = STROKES_AT(t)
            if t < LAID[6][1]:
                lay(cv, body_img(*nd), WORK[0], WORK[1], WORK_R, 1.0)
            else:
                x, y, r, lift = flight(t, LAID[6][1], LAID[6][2], WORK, BOX, BOX_R)
                r = lerp(WORK_R, BOX_R, ease(t, LAID[6][1], LAID[6][2])) + spring(t, LAID[6][2], 1.2, 5, 9)
                lay(cv, body_img(len(STROKES), 0.0), x, y, r, lift)
    # the hinged things
    if t >= T_DOOR[0]:
        f = ease(t, *T_DOOR)
        x, y = lerp2((1320, 1300), HINGE, f)
        lay(cv, A["door"], x, y, door_state(t) + 30 * (1 - f), 1.2 + 20 * (1 - f), pivot=A["door_pivot"])
    for tp, x, y, kind in PINS:
        draw_pin(cv, t, tp, x, y, kind)
    return cv


def STROKES_AT(t):
    """How much of the number is painted at time t: (whole strokes, fraction of the next)."""
    n = len(STROKES)
    f = ramp(t, *T_INK) * n
    k = min(n, int(f))
    part = f - k
    return (k, 0.0) if k >= n else (k, min(1.0, part / 0.72))      # the brush lifts between strokes


# ---- over the gel: letters, trout, bubbles, the tin ------------------------------

TIN_AT = (1662, 500)             # critic: further into frame, so the tin and its ROLLS label read
TS = 1.25                       # the tin is laid down a quarter larger than it was built
MOUTH_OFF = (108, 6)


def tin_pos(t):
    v = twos(t) - T2
    x = keys(v, [(0.2, 2560.0), (2.6, TIN_AT[0])])[0]
    return x, TIN_AT[1] + 3.0 * math.sin(v * 1.3)


def nozzle(t):
    x, y = tin_pos(t)
    return x + TS * (TIN_NOZZLE[0] - 4 - (TIN_W + 2 * TIN_PAD) / 2), y + TS * (TIN_NOZZLE[1] - (TIN_H + 2 * TIN_PAD) / 2)


HAND = (TIN_AT[0] + TS * (TIN_NOZZLE[0] - 4 - (TIN_W + 2 * TIN_PAD) / 2) - MOUTH_OFF[0] - 10, TIN_AT[1] + TS * (TIN_NOZZLE[1] - (TIN_H + 2 * TIN_PAD) / 2) + 2)   # where a trout holds a letter up to the intake


def trout_a(t):
    """(x, y, flipped) flipped = facing right."""
    if t < T1:
        f = ease(t, 13.05, 13.7)
        x, y = lerp2((2300, 900), TROUT_A, f)
        return x, y, False, 1 + 16 * (1 - f)
    tt = twos(t)
    if tt < T2:
        u = tt - T1
        if u < 2.7:
            x, y = keys(u, [(1.0, *TROUT_A), (1.8, 1324.0, 846.0), (2.6, 1350.0, 834.0)])
            return x, y, False, 1.5
        x, y = keys(u, [(2.7, 1350.0, 834.0), (5.6, 1780.0, 600.0)])
        return x, y, True, 1.5
    v = tt - T2
    if v < 4.1:
        x, y = keys(v, [(0.0, 1040.0, 640.0), (2.4, HAND[0], HAND[1]), (4.1, HAND[0] - 4, HAND[1] + 4)])
        return x, y, True, 1.5
    x, y = keys(v, [(4.1, HAND[0] - 4, HAND[1] + 4), (6.8, 840.0, 236.0), (10.0, 800.0, 250.0)])
    return x, y, False, 1.5


def trout_b(t):
    tt = twos(t)
    if tt < T1 + 5.0:
        return None
    if tt < T2:
        u = tt - T1
        if u < 8.2:
            x, y = keys(u, [(5.0, 1760.0, 660.0), (7.0, 1298.0, 768.0), (7.4, 1280.0, 766.0), (8.2, 1304.0, 756.0)])
            return x, y, False, 1.5
        x, y = keys(u, [(8.2, 1304.0, 756.0), (10.0, 1440.0, 700.0)])
        return x, y, True, 1.5
    v = tt - T2
    if v < 7.1:
        x, y = keys(v, [(0.0, 1110.0, 800.0), (3.6, 1090.0, 600.0), (5.7, HAND[0], HAND[1]), (7.1, HAND[0] - 4, HAND[1] + 4)])
        return x, y, True, 1.5
    x, y = keys(v, [(7.1, HAND[0] - 4, HAND[1] + 4), (10.0, 960.0, 620.0)])
    return x, y, False, 1.5


def mouth_of(st):
    x, y, fl, _ = st
    return (x + MOUTH_OFF[0] if fl else x - MOUTH_OFF[0]), y + MOUTH_OFF[1]


GRAB = {4: T1 + 1.8, 2: T1 + 7.4}                 # letter -> when a trout takes it
GIVE = {4: (T2 + 3.0, T2 + 3.7), 2: (T2 + 6.0, T2 + 6.7)}        # letter -> when it is handed to the tin
DRAWN = {1: (T2 + 4.4, T2 + 5.5), 3: (T2 + 6.9, T2 + 8.0), 0: (T2 + 7.8, T2 + 8.9)}   # letter -> lifted off toward the intake


def letter_state(k, t):
    """(x, y, rot, lift) or None once it has gone into the tin."""
    key, x0, y0, r0, td = LETTERS[k]
    if t < td:
        return None
    if t < T1 and t < td + 0.6:
        f = ease(t, td, td + 0.42)
        x, y = lerp2((2100, 1240), (x0, y0), f)
        return x, y, r0 + 60 * (1 - f) + spring(t, td + 0.42, 4, 5, 8), 1 + 24 * (1 - f)
    tt = twos(t)
    if k == 0 and tt >= T1 + 3.2:                 # shaken a little further out when the sack lurches
        f = ease(tt, T1 + 3.2, T1 + 4.2)
        x0, y0, r0 = x0 + 26 * f, y0 + 34 * f, r0 + 15 * f
    if k in GRAB and tt >= GRAB[k]:
        carrier = trout_a(t) if k == 4 else trout_b(t)
        g0, g1 = GIVE[k]
        mx, my = mouth_of(carrier)
        rot = 24.0 if carrier[2] else -24.0
        if tt < g0:
            return mx, my, rot, 3.0
        if tt >= g1:
            return None
        f = ease(tt, g0, g1)
        nx, ny = nozzle(t)
        x, y = lerp2((mx, my), (nx + 40, ny), f)
        return x, y, rot * (1 - f), 3.0
    if k in DRAWN and tt >= DRAWN[k][0]:
        d0, d1 = DRAWN[k]
        if tt >= d1:
            return None
        f = ramp(tt, d0, d1)
        nx, ny = nozzle(t)
        g = f * f * (3 - 2 * f)
        x = lerp(x0, nx + 40, g ** 1.5)
        y = lerp(y0, ny, g) - 70 * math.sin(math.pi * g) * (1 - g)
        return x, y, r0 + 200 * g * (1 if k % 2 else -1), 1 + 12 * math.sin(math.pi * min(1, f * 1.4))
    return x0, y0, r0, 1.0


BUBBLES = [   # (born, x, y, size) hole-punch dots, moved up the board a notch at a time
    (T1 + 1.9, 1236, 836, 0), (T1 + 2.1, 1250, 850, 1),
    (T1 + 3.3, 1060, 770, 1), (T1 + 3.5, 1086, 790, 2), (T1 + 3.8, 1040, 780, 0), (T1 + 4.4, 1100, 800, 1),
    (T1 + 7.5, 1190, 756, 0), (T1 + 7.7, 1204, 770, 1), (T1 + 8.6, 1070, 780, 2),
    (T2 + 2.7, 1060, 770, 1), (T2 + 3.0, 1090, 790, 0),
    (T2 + 3.7, 1220, 330, 2), (T2 + 3.9, 1240, 312, 0), (T2 + 4.1, 1210, 322, 1),
    (T2 + 5.5, 1230, 330, 1), (T2 + 6.7, 1220, 330, 2), (T2 + 6.9, 1242, 314, 0), (T2 + 8.0, 1220, 328, 1), (T2 + 8.9, 1230, 330, 2),
]


def over_gel(cv, t):
    part3 = t >= T2
    tt = twos(t) if t >= T1 else t
    if t >= T_SACK[0]:                                     # the sack: on top of the gel, hung from the box's mouth
        f = ease(t, *T_SACK)
        x, y = lerp2((1500, 1300), SACKP, f)
        lay(cv, A["sack"], x, y, sack_state(t) + 24 * (1 - f), 2.0 + 20 * (1 - f), pivot=A["sack_pivot"])
    if t >= T_FLAG[0]:                                     # the red flag, on its own brass fastener, over the gel too
        f = ease(t, *T_FLAG)
        x, y = lerp2((700, -200), FLAGP, f)
        lay(cv, A["flag"], x, y, flag_state(t) - 30 * (1 - f), 1.6 + 20 * (1 - f), pivot=A["flag_pivot"])
        draw_pin(cv, t, T_FLAG[1] + 0.06, FLAGP[0], FLAGP[1], "brad")
    # loose letters first (they lie on the gel), then anything in a mouth or on its way to the tin
    states = [letter_state(k, t) for k in range(len(LETTERS))]
    for k, st in enumerate(states):
        if st is not None and st[3] <= 1.0:
            lay(cv, A[LETTERS[k][0]], st[0], st[1], st[2], st[3])
    for born, x, y, sz in BUBBLES:
        age = tt - born
        if 0 <= age < 5.0:
            lay(cv, A[f"dot{sz}"], x + 14 * math.sin(age * 2.2 + sz), y - 52 * age - 6 * age * age, 0, 1.0)
    for k, st in enumerate(states):
        if st is not None and st[3] > 1.0:
            lay(cv, A[LETTERS[k][0]], st[0], st[1], st[2], st[3])
    if part3:
        x, y = tin_pos(t)
        v = t - T2
        spr = tin_sprite(t, duck=spring(t, T2 + 2.6, 14, 1.4, 2.0), wattle=14 * math.sin(t * 2.0) * 0.4 + spring(t, T2 + 2.6, 26, 1.7, 1.5))
        lay(cv, spr, x, y, spring(t, T2 + 2.6, 1.6, 1.2, 2.2), 5.0)
    for fn, ph in ((trout_a, 0.0), (trout_b, 1.7)):
        st = fn(t)
        if st is None:
            continue
        x, y, fl, lift = st
        spr = flex(A["trout"], tt * 7.0 + ph, 9.0)
        if fl:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        lay(cv, spr, x, y + 3 * math.sin(tt * 1.9 + ph), 3.0 * math.sin(tt * 1.3 + ph), lift)
    if part3:                                              # the watcher in the foreground
        v = tt - T2
        x = keys(v, [(0.0, -380.0), (1.6, 300.0)])[0]
        spr = flex(A["trout_big"], tt * 5.0 + 3.0, 10.0).transpose(Image.FLIP_LEFT_RIGHT)
        lay(cv, spr, x, 872 + 4 * math.sin(tt * 1.5), 8.0 + 3 * math.sin(tt * 1.1), 3.0)


def tools(cv, t):
    """Pencil, scissors, brush: each comes in from the lower right, does its work, and is taken away."""
    home = (2150, 1260)
    loop = OUTLINE + OUTLINE[:1]
    if T_DRAW[0] - 0.4 <= t < T_DRAW[1] + 0.4:
        p, _ = path_at(loop, ramp(t, *T_DRAW))
        tip = sheet_pt(p[0], p[1], WORK, WORK_R)
        fin, fout = ease(t, T_DRAW[0] - 0.4, T_DRAW[0]), ease(t, T_DRAW[1], T_DRAW[1] + 0.4)
        x, y = lerp2(lerp2(home, tip, fin), home, fout)
        lay(cv, A["pencil"], x, y, -38 + 5 * math.sin(t * 9), 10 + 14 * (1 - fin) + 14 * fout, pivot=(0, 14))
    if T_CUT[0] - 0.45 <= t < T_CUT[1] + 0.45:
        cutpath = ENTRY + OUTLINE[1:] + OUTLINE[:1]
        f = ramp(t, *T_CUT)
        p, head = path_at(cutpath, f)
        p2, head2 = path_at(cutpath, clamp(f + 0.03))
        head = head2
        tip = sheet_pt(p[0], p[1], WORK, WORK_R)
        hd = head - WORK_R
        # the hand does not swing the shears right round: it turns them through the easy half and the paper does the rest
        swing = ((hd + 180) % 360) - 180
        ang = clamp(swing, -150, 60) * 0.55 - 150
        ar = math.radians(ang)
        piv = (tip[0] - 190 * math.cos(ar), tip[1] - 190 * math.sin(ar))
        fin, fout = ease(t, T_CUT[0] - 0.45, T_CUT[0]), ease(t, T_CUT[1], T_CUT[1] + 0.45)
        x, y = lerp2(lerp2(home, piv, fin), home, fout)
        op = 7 + 17 * abs(math.sin(math.pi * 3.2 * (t - T_CUT[0]))) if T_CUT[0] <= t <= T_CUT[1] else 16
        spr, pv = scissors_img(op)
        lay(cv, spr, x, y, -ang, 14, pivot=pv)
    if T_INK[0] - 0.35 <= t < T_INK[1] + 0.4:
        k, part = STROKES_AT(max(t, T_INK[0]))
        k = min(k, len(STROKES) - 1)
        st = STROKES[k]
        pts = catmull(st, 6) if len(st) > 2 else st
        p, _ = path_at(pts, min(1.0, part))
        f = ramp(t, *T_INK) * len(STROKES)
        lifted = (f - int(f)) > 0.72 or t < T_INK[0] or t > T_INK[1]
        tip = sheet_pt(p[0], p[1], WORK, WORK_R)
        fin, fout = ease(t, T_INK[0] - 0.35, T_INK[0]), ease(t, T_INK[1], T_INK[1] + 0.4)
        x, y = lerp2(lerp2(home, tip, fin), home, fout)
        lay(cv, A["brush"], x, y - (10 if lifted else 0), -42, (16 if lifted else 5) + 14 * (1 - fin) + 14 * fout, pivot=(0, 16))


# ================================================================ the three parts ===

def table(t):
    """The whole board at time t, as a float RGB array (2 table px per screen px)."""
    cv = under_gel(t)
    gel_on = t >= T_GEL[0]
    if not gel_on:
        tools(cv, t)
        a = np.asarray(cv.convert("RGB"), np.float32)
        return a
    a = np.asarray(cv.convert("RGB"), np.float32).copy()
    front = None
    if t < T_GEL[1] + 0.1:
        front = lerp(20, WH + 80, ease(t, *T_GEL))
    apply_gel(a, t, front, glint=1.0 if t < T1 else 1.25)
    top = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    over_gel(top, t)
    for tp, x, y in GEL_PINS:
        draw_pin(top, t, tp, x, y, "pin")
    ta = np.asarray(top, np.float32)
    al = ta[..., 3:4] / 255.0
    a = a * (1 - al) + ta[..., :3] * al
    return a


def lamp_pool(t):
    """Part three: the room lamp is off; the only light is the tin's lamp, thrown across the gel."""
    x, y = tin_pos(t)
    lx = x + TS * (TIN_LAMP[0] - 20 - (TIN_W + 2 * TIN_PAD) / 2)
    ly = y + TS * (TIN_LAMP[1] - 16 - (TIN_H + 2 * TIN_PAD) / 2)
    S = 8
    m = Image.new("L", (WW // S, WH // S), 0)
    d = ImageDraw.Draw(m)
    ang = math.radians(163 + 7 * math.sin((t - T2) * 0.7))
    for half, val in ((0.42, 110), (0.26, 190), (0.13, 255)):
        p1 = (lx + 1700 * math.cos(ang - half), ly + 1700 * math.sin(ang - half))
        p2 = (lx + 1700 * math.cos(ang + half), ly + 1700 * math.sin(ang + half))
        d.polygon([(lx / S, ly / S), (p1[0] / S, p1[1] / S), (p2[0] / S, p2[1] / S)], fill=val)
    d.ellipse([lx / S - 14, ly / S - 14, lx / S + 14, ly / S + 14], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(9)).resize((WW, WH), Image.BILINEAR)
    g = np.asarray(m, np.float32) / 255
    dist = np.hypot(A["xx"] - lx, A["yy"] - ly)
    return g * np.clip(1.15 - dist / 1500.0, 0.15, 1)


def to_screen(a):
    return to_img(a).reduce(2)


def part1(t):
    a = table(t) * A["lamp1"]
    return to_screen(a)


def part2(t):
    a = table(t)
    half = RG / VIEW_S
    x0, y0 = int(VIEW_C[0] - half), int(VIEW_C[1] - half)
    crop = to_img(a[y0:y0 + int(2 * half), x0:x0 + int(2 * half)]).resize((2 * RG, 2 * RG), Image.LANCZOS)
    g = np.asarray(crop, np.float32) * A["glass_dark"] * 1.06
    view = to_img(g).convert("RGBA")
    view.alpha_composite(A["glass_hi"])
    fr = A["wall"].copy()
    fr.paste(view, (PC[0] - RG, PC[1] - RG), A["glass_mask"])
    rg = A["ring_big"]
    fr.alpha_composite(rg, (PC[0] - rg.width // 2, PC[1] - rg.height // 2))
    # Turkey at the glass: lit from his own lamp, the wattle a beat behind the head
    u = t - T1
    lean = keys(u, [(0.0, -60.0, 30.0), (1.4, 0.0, 0.0), (3.1, 0.0, 0.0), (3.6, 16.0, -8.0), (7.2, 14.0, -6.0), (7.8, 24.0, -12.0), (10.0, 20.0, -10.0)])
    wat = 5 * math.sin(t * 1.7) + spring(t, T1 + 1.4, 22, 1.6, 1.6) + spring(t, T1 + 3.6, 18, 1.6, 1.6) + spring(t, T1 + 7.8, 14, 1.6, 1.6)
    tk = turkey_img(wat, 470)
    sh = shadow_of(tk, 9, 0.6, (0, 0, 0))
    px, py = int(-52 + lean[0]), int(128 + lean[1] + 3 * math.sin(t * 1.1))
    paste_clip(fr, sh, px + 16, py + 12)
    paste_clip(fr, tk, px, py)
    return fr.convert("RGB")


def part3(t):
    a = table(t)
    pool = lamp_pool(t)[..., None]
    a = a * (np.array([0.40, 0.52, 0.60], np.float32) + pool * np.array([1.25, 1.02, 0.66], np.float32)) + pool * np.array([40, 30, 8], np.float32)
    return to_screen(a)


CAPTIONS = [
    (0.9, 4.2, "Prints from the Farm Security file: Rothstein, Vachon, Delano, Lee. 1940 and 1941."),
    (5.0, 9.4, "Box 44: blue paper, cut along a pencil line, numbered with a brush."),
    (10.5, 13.7, "The river is one sheet of green gel. Lee's mail bag, cut from its print, goes in last."),
    (T1 + 1.6, T2 - 0.5, "Are those my lost mission orders? Or is that only a sack of laundry?"),
    (T2 + 2.6, SECONDS - 0.5, "A porch pirate with a vacuum? Or the mailman's truck, here at last?"),
]


def picture(t, ink):
    img = part1(t) if t < T1 else part2(t) if t < T2 else part3(t)
    for cut in (T1, T2):                                   # a two-frame dip at each cut, nothing fancier
        if abs(t - cut) < 0.09 or (cut - 0.2 < t < cut):
            k = 0.35 if abs(t - cut) < 0.09 else lerp(1.0, 0.35, (t - cut + 0.2) / 0.2)
            img = Image.eval(img, lambda v, k=k: int(v * k))
    if t < 0.4:
        img = Image.eval(img, lambda v, k=t / 0.4: int(v * k))
    if t > SECONDS - 0.5:
        img = Image.eval(img, lambda v, k=(SECONDS - t) / 0.5: int(v * max(0.0, k)))
    ink.img = img.convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink._grain = False                                     # no added grain: the grain on screen is the photographs' own
    for a, b, s in CAPTIONS:
        if a <= t < b:
            ink.caption(s, alpha=min(1.0, (t - a) / 0.3, (b - t) / 0.3), size=23)


def build():
    t0 = time.time()
    build_board()
    yy, xx = np.mgrid[0:WH, 0:WW].astype(np.float32)
    A["xx"] = xx
    build_prints()
    build_trout()
    A["trout_big"] = bevel(A["trout_full"].resize((440, int(440 * A["trout_full"].height / A["trout_full"].width)), Image.LANCZOS), 30, 40)
    build_turkey()
    build_box()
    build_letters()
    build_pins()
    build_tools()
    build_gel()
    build_tin()
    build_sack()
    build_port()
    build_stage()
    print(f"built in {time.time() - t0:.1f}s", flush=True)


def sound(mix):
    """Synthesized from the same timetable the picture runs on: every sound is a piece arriving, a tool
    working, a pin going in, a letter changing holder. No music."""
    rs = np.random.RandomState(35)

    def paper(at, dur=0.5, gain=0.05, pan=0.0, bright=5200):
        n = int(dur * mix.rate)
        x = mix.band(mix.noise(dur), 900, bright) * np.hanning(n) ** 1.5
        mix.add(x, at, gain, pan)

    def tap(at, gain=0.12, pan=0.0):
        mix.thud(at, 120, gain, pan, 0.12)
        mix.click(at, gain * 0.5, pan, 2600, 0.02)

    def pin(at, pan=0.0):
        mix.click(at, 0.2, pan, 6500, 0.018)
        mix.thud(at + 0.01, 190, 0.16, pan, 0.09)

    def bubble(at, pan=0.0, gain=0.05):
        tt = mix.t(0.11)
        f0 = rs.uniform(500, 900)
        mix.add(np.sin(2 * np.pi * (f0 + 2600 * tt) * tt) * np.exp(-tt * 28), at, gain, pan)

    def pan_of(x):
        return clamp(x / WW * 2 - 1, -1, 1) * 0.7

    # ---- part one: the room, and the work
    mix.room(0.0, T1 + 0.2, gain=0.016)
    for key, t0, t1, s_, d_, r_ in LAID:
        paper(t0, t1 - t0, 0.05, pan_of(d_[0]))
        tap(t1, 0.1, pan_of(d_[0]))
    paper(T_SHEET[0], 0.7, 0.05, 0.4)
    tap(T_SHEET[1], 0.08, 0.3)
    for tp, x, y, kind in PINS:
        pin(tp + 0.1, pan_of(x))
    n = int((T_DRAW[1] - T_DRAW[0]) * mix.rate)                       # the pencil: a dry hiss that follows the hand's speed
    tt = np.arange(n) / mix.rate
    scratch = mix.band(mix.noise(T_DRAW[1] - T_DRAW[0]), 2500, 7000) * (0.55 + 0.45 * np.sin(2 * np.pi * 5.3 * tt)) * np.hanning(n) ** 0.3
    mix.add(scratch, T_DRAW[0], 0.035, 0.3)
    k = 0
    while T_CUT[0] + k / 3.2 < T_CUT[1]:                              # the shears: one bite per closing of the blades
        at = T_CUT[0] + k / 3.2
        x = mix.band(mix.noise(0.2), 1800, 8000) * np.linspace(0.2, 1, int(0.2 * mix.rate)) ** 2
        mix.add(x, at + 0.06, 0.07, 0.3)
        mix.click(at + 0.26, 0.22, 0.3, 7000, 0.02)
        mix.note(at + 0.26, 2900 + 200 * (k % 2), 0.05, 0.03, 0.3, "sine", 0.001, 0.04, 0.0)
        k += 1
    paper(T_WASTE[0], 0.6, 0.06, 0.6)
    for q in range(len(STROKES)):                                     # the brush: eight soft strokes
        at = T_INK[0] + q * (T_INK[1] - T_INK[0]) / len(STROKES)
        d_ = 0.72 * (T_INK[1] - T_INK[0]) / len(STROKES)
        x = mix.band(mix.noise(d_), 300, 1600) * np.hanning(int(d_ * mix.rate))
        mix.add(x, at, 0.07, 0.3)
    pin(12.72, 0.0)
    pin(T_FLAG[1] + 0.16, -0.5)
    for t0, t1 in (T_DOOR, T_FLAG, T_SACK):
        paper(t0, t1 - t0, 0.045, -0.2)
        tap(t1, 0.09, -0.2)
    n = int((T_GEL[1] - T_GEL[0]) * mix.rate)                         # the gel: a long crackle of acetate
    cr = np.zeros(n)
    for _ in range(260):
        i = rs.randint(0, n - 400)
        cr[i:i + 300] += rs.uniform(0.3, 1.0) * mix.noise(300 / mix.rate)[:300] * np.exp(-np.linspace(0, 9, 300))
    mix.add(mix.band(cr, 2000, 9000) * np.hanning(n) ** 0.4, T_GEL[0], 0.09, 0.0)
    paper(T_GEL[0], T_GEL[1] - T_GEL[0], 0.04, 0.0, 2500)
    for tp, x, y in GEL_PINS:
        pin(tp + 0.1, pan_of(x))
    for key, x, y, r, td in LETTERS:
        paper(td, 0.4, 0.035, pan_of(x), 7000)
        mix.click(td + 0.42, 0.1, pan_of(x), 3000, 0.02)
    paper(13.05, 0.65, 0.04, 0.5)
    tap(13.7, 0.08, 0.4)
    # ---- part two: inside the tin. The hull hums, the water is on the other side of the glass
    mix.thud(T1, 55, 0.3, 0.0, 0.5)
    mix.drone(T1, T2 - T1 + 0.3, (49, 73.5, 98), 0.05, 0.0, 0.6, 0.8)
    hum = mix.tone(61, T2 - T1, "saw") * (0.7 + 0.3 * np.sin(2 * np.pi * 7.5 * mix.t(T2 - T1)))
    mix.add(mix.lowpass(hum, 400) * mix.env(len(hum), 0.5, 0.01, 1.0, 0.5), T1, 0.035, -0.5)
    w = mix.lowpass(mix.noise(T2 - T1, "pink"), 500)
    mix.add(w * mix.env(len(w), 0.6, 0.01, 1.0, 0.6), T1, 0.05, 0.2)
    for tg, pan in ((GRAB[4], 0.3), (GRAB[2], 0.3)):                  # a trout takes a letter: the hand-off
        mix.thud(tg, 150, 0.12, pan, 0.14)
        paper(tg, 0.16, 0.03, pan, 2000)
    for tk, amp in KICKS:
        mix.thud(tk, 62, 0.2, -0.2, 0.4)
        paper(tk + 0.05, 0.5, 0.025, -0.1, 1500)
    mix.murmur(T1 + 1.7, 3.4, 0.045, 150, -0.6, seed=4)               # Turkey, wondering aloud (not speech)
    # ---- part three: out in the water
    mix.thud(T2, 60, 0.26, 0.0, 0.5)
    mix.water(T2, SECONDS - T2, 0.05)
    mix.drone(T2, SECONDS - T2, (55, 82.5), 0.035, 0.0, 0.5, 1.2)
    d_ = 3.0                                                          # the tin comes in: its screw, louder, then stopped
    mot = mix.tone(74, d_, "saw") * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 11 * mix.t(d_))))
    mot = mix.lowpass(mot, 900) * np.linspace(0.05, 1, len(mot)) ** 1.5
    mot[-int(0.35 * mix.rate):] *= np.linspace(1, 0, int(0.35 * mix.rate))
    mix.add(mot, T2 + 0.1, 0.07, 0.7)
    mix.thud(T2 + 2.62, 70, 0.3, 0.6, 0.4)
    mix.bell(T_FLAG_UP + 0.3, 1568, 1.6, 0.12, -0.5)                  # the flag goes up
    tap(T_FLAG_UP + 0.33, 0.1, -0.5)
    for k, (g0, g1) in list(GIVE.items()) + list(DRAWN.items()):      # each letter into the intake: a draw of water, a knock in the pipe
        dd = g1 - g0
        x = mix.band(mix.noise(dd), 400, 3000) * np.linspace(0.1, 1, int(dd * mix.rate)) ** 2
        mix.add(x, g0, 0.05, 0.4)
        mix.thud(g1, 210, 0.14, 0.45, 0.1)
        mix.click(g1 + 0.02, 0.1, 0.45, 2500, 0.03)
    for born, x, y, sz in BUBBLES:
        bubble(born, pan_of(x), 0.035 if born < T2 else 0.05)
    mix.murmur(T2 + 2.8, 3.2, 0.04, 250, -0.4, seed=9)                # the trout, to each other
    mix.reverb(0.12, 0.8)
    peak = max(np.abs(mix.L).max(), np.abs(mix.R).max())
    mix.L *= 0.84 / peak
    mix.R *= 0.84 / peak


def main():
    build()
    film = Film(SLUG, SECONDS, boil=0, wobble=0.0)
    film.poster_at = T1 + 2.0
    film.picture(picture)
    film.sound(sound)
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        times = [float(x) for x in sys.argv[2:]]
        contact(SLUG, cols=3, scale=0.5, times=times or None)


if __name__ == "__main__":
    main()
