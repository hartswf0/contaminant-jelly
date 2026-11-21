"""props.py · the things of THE DOGS OF TROUTTOWN.

Everything a dog digs up, carries, lays down or breathes out, drawn onto the kit's Ink (or a PIL image):

    reel            a film can a dog carries in its mouth, lays on the sill and stacks; its face shows ONE
                    real frame of the real film it holds (REELS, in the order of scion/WHAT_WE_MADE.md)
    part            a dripping part from the gravel (gear, spool, flange, crank, lens, strip)
    page            a child's page with the ring on it, carried flat and never bent; blank_page the same, empty
    paw_print       one thing written; it stays
    lantern         for the dog that swims out past the last streetlight
    pile            the small wet pile that grows on the sill; reel_piles the 53 cans of the last shot
    picture_bubble  a bubble with a picture inside
    ice_sheet       the water frozen over; freezes, is stamped, cracks, breaks up
    breath          breath bubbles that run out

All positions are SCREEN pixels. `s` is the same scale the dogs use (dog.py: 1.0 = one dog unit per pixel,
0.6 in the porch two-shot, 1.6 close). Things under water take tint=TEAL, tint_amount=0.35 like the dogs do
(or **UNDER). The *_sprite functions return RGBA images for dog.draw_dog(carry=...): the grip is the middle
of the top edge, which is where dog.py puts the mouth.

    python3 films/swarm/dogs/props.py            # frames (if missing) + the sheets, and the self-test
    python3 films/swarm/dogs/props.py --frames   # re-cut the reel frames from the films with ffmpeg

Handmade from code, except the reel faces, which are frames of this project's own films.
"""

from __future__ import annotations

import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
PROJECT = FILMS.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import clamp, ramp, smooth, ease, lerp, mix_color  # noqa: E402

FRAMES = HERE / "frames"
TAU = 2 * math.pi

# ----------------------------------------------------------------- colours ---
EDGE = (58, 30, 12)             # the dog's paper edge
TEAL = (24, 120, 128)
AMBER = (255, 188, 98)
UNDER = dict(tint=TEAL, tint_amount=0.35)
PAPER = (250, 246, 233)
PAPER_WET = (196, 206, 196)
PENCIL = (52, 54, 66)
PRINT = (150, 150, 162)         # the ring printed on the class page
METAL = (186, 194, 202)
METAL_DARK = (96, 104, 122)
FILM = (44, 40, 50)
BRASS = (204, 160, 72)
BRASS_DARK = (128, 92, 40)
MUD = (86, 70, 52)
WEED = (52, 110, 72)
WATERDROP = (206, 232, 240)
ICE = (222, 240, 246)
ICE_BLUE = (150, 196, 214)
BUBBLE = (234, 248, 244)

# ------------------------------------------------------------------- reels ---
# The reels on the sill are the real films, in the order of scion/WHAT_WE_MADE.md. 53 reels were carried up
# (thick prompt, part 8). Each row: (file under assets/, seconds into it, where the round face looks: centre x
# and centre y as fractions of the frame, and how much of the frame's height the face takes), then what it is.
REELS = [
    # 4 · five hand films, then cut together
    ("films/p01.mp4", 16.0, 0.50, 0.50, 1.00, "Porthole 01, the scissors film: the boot seen through the brass porthole"),
    ("films/p03.mp4", 17.0, 0.42, 0.50, 1.00, "Porthole 03, the chalk film: HOOK MONSTER on the slate, in the porthole"),
    ("films/p14.mp4", 17.0, 0.50, 0.50, 1.00, "Porthole 14, the scalpel film: the red leaf and the trout in the porthole"),
    ("films/p35.mp4", 17.0, 0.47, 0.50, 1.00, "Porthole 35, the pins film: the pinned photographs under green water"),
    ("films/p44.mp4", 17.0, 0.48, 0.50, 1.00, "Porthole 44, the pen film: the spiral disc in the porthole"),
    ("voiced/p01.mp4", 27.0, 0.50, 0.50, 1.00, "Porthole 01 with the voice: the boot standing in the river, the sub below"),
    ("voiced/p03.mp4", 30.0, 0.30, 0.42, 0.84, "Porthole 03 with the voice: the slate in the river"),
    ("voiced/p14.mp4", 30.0, 0.55, 0.50, 1.00, "Porthole 14 with the voice: the leaf, the trout and the sub in the river"),
    ("voiced/p35.mp4", 30.0, 0.40, 0.55, 0.90, "Porthole 35 with the voice: a trout swims past the pinned photographs"),
    ("voiced/p44.mp4", 26.0, 0.40, 0.50, 1.00, "Porthole 44 with the voice: the disc on its stand in the river"),
    ("nobody-is-holding-the-chalk.mp4", 182.0, 0.42, 0.50, 1.00, "Nobody Is Holding the Chalk: the slate in the river (reel one)"),
    ("nobody-is-holding-the-chalk.mp4", 128.0, 0.18, 0.47, 0.94, "Nobody Is Holding the Chalk: the spiral disc on the desk (reel two)"),
    # 5 · five class films, from the pages a fourth-grade class filled in
    ("films/c10.mp4", 13.0, 0.42, 0.50, 1.00, "Class film 10: Turkey in the porthole, the locked school"),
    ("films/c13.mp4", 26.0, 0.50, 0.50, 1.00, "Class film 13: two fish and the dinner bell"),
    ("films/c16.mp4", 20.0, 0.62, 0.50, 1.00, "Class film 16: the three-headed monster"),
    ("films/c25.mp4", 26.0, 0.42, 0.50, 1.00, "Class film 25: the fish with arms and legs, painting"),
    ("films/c33.mp4", 35.0, 0.47, 0.50, 1.00, "Class film 33: the bars across the window, a movie"),
    ("voiced/c10.mp4", 7.6, 0.41, 0.48, 0.90, "Class film 10 with the voice: the child's page, zigzag teeth in a box"),
    ("voiced/c13.mp4", 6.0, 0.42, 0.50, 0.92, "Class film 13 with the voice: the child's page, two fish and a bell"),
    ("voiced/c16.mp4", 6.0, 0.36, 0.50, 0.92, "Class film 16 with the voice: the child's page, the boxy sub"),
    ("voiced/c25.mp4", 6.0, 0.42, 0.52, 0.92, "Class film 25 with the voice: the child's page, the fish across a bowl"),
    ("voiced/c33.mp4", 7.0, 0.38, 0.50, 0.92, "Class film 33 with the voice: the child's page, the tall bars"),
    # 6 · the five cut into one, with the steps taught
    ("how-to-play-the-porthole-game.mp4", 165.0, 0.52, 0.47, 0.90, "How to Play the Porthole Game: the fish and the bell (reel one)"),
    ("how-to-play-the-porthole-game.mp4", 53.0, 0.44, 0.45, 0.80, "How to Play the Porthole Game: the pilot draws what is outside (reel two)"),
    ("how-to-play-the-porthole-game.mp4", 355.0, 0.47, 0.47, 0.90, "How to Play the Porthole Game: the bars (reel three)"),
    # 7 · five making films, the children at the desk; then The Class Plays
    ("films/m10.mp4", 11.0, 0.42, 0.50, 1.00, "Making film 10: a cut-paper hand draws the zigzag teeth"),
    ("films/m13.mp4", 11.0, 0.50, 0.50, 1.00, "Making film 13: the two fish coming up out of the page"),
    ("films/m16.mp4", 11.0, 0.42, 0.50, 1.00, "Making film 16: the boxy sub coming up out of the page"),
    ("films/m25.mp4", 11.0, 0.50, 0.50, 1.00, "Making film 25: the fish with legs coming up out of the page"),
    ("films/m33.mp4", 11.0, 0.50, 0.50, 1.00, "Making film 33: the bars and the fish coming up out of the page"),
    ("voiced/m10.mp4", 69.0, 0.50, 0.50, 1.00, "Making film 10 with the voice: out into the river, the sub and the shell"),
    ("voiced/m13.mp4", 22.0, 0.40, 0.50, 1.00, "Making film 13 with the voice: an orange paper hand writes the sentence"),
    ("voiced/m16.mp4", 68.0, 0.50, 0.50, 1.00, "Making film 16 with the voice: out into the river"),
    ("voiced/m25.mp4", 70.0, 0.55, 0.55, 0.90, "Making film 25 with the voice: the sub's brass door in the river"),
    ("voiced/m33.mp4", 68.0, 0.62, 0.50, 1.00, "Making film 33 with the voice: the sub's lamp on the bars"),
    ("tourkey-trouttown-the-class-plays.mp4", 252.0, 0.50, 0.50, 1.00, "Tourkey Trouttown: The Class Plays (reel one): the trout in the porthole"),
    ("tourkey-trouttown-the-class-plays.mp4", 380.0, 0.50, 0.47, 0.90, "The Class Plays (reel two): a paper hand at the page"),
    ("tourkey-trouttown-the-class-plays.mp4", 507.0, 0.50, 0.47, 0.90, "The Class Plays (reel three): the three-headed monster in the porthole"),
    ("tourkey-trouttown-the-class-plays.mp4", 634.0, 0.45, 0.47, 0.90, "The Class Plays (reel four): a wall of small cards"),
    ("tourkey-trouttown-the-class-plays.mp4", 760.0, 0.78, 0.47, 0.90, "The Class Plays (reel five): a paper hand writes under the bars"),
    # 9 · films about how it works
    ("how-a-language-model-makes-a-film.mp4", 106.0, 0.29, 0.56, 0.52, "How a Language Model Makes a Film: the porthole the judge looked at"),
    ("who-held-the-chalk.mp4", 110.0, 0.80, 0.55, 0.70, "Who Held the Chalk: the pinned photographs that were foraged"),
    ("what-is-a-scion.mp4", 56.0, 0.50, 0.50, 1.00, "What Is a SCION? (reel one): the river built in planes"),
    ("what-is-a-scion.mp4", 180.0, 0.25, 0.52, 0.70, "What Is a SCION? (reel two): the swarm at its desks"),
    ("dont-pave-the-cow-paths.mp4", 285.0, 0.42, 0.30, 0.60, "Don't Pave the Cow Paths (reel one): the cows in single file on the bank"),
    ("dont-pave-the-cow-paths.mp4", 98.0, 0.70, 0.47, 0.80, "Don't Pave the Cow Paths (reel two): the scion, a shoot cut from one tree"),
    # 10 · the conversation itself
    ("behind-the-chat.mp4", 150.0, 0.40, 0.50, 1.00, "Behind the Chat: the conversation as a scrolling log"),
    ("behind-the-chat-dogs.mp4", 26.0, 0.50, 0.50, 1.00, "Behind the Chat, with Dogs: the porch at dusk, the person and the dog"),
    # 11 · the cow-path cartoon, three studies and two acts so far
    ("films/cowpath-study-line.mp4", 11.0, 0.86, 0.50, 0.80, "Cow-path study, the line: the stump that sprouts"),
    ("films/cowpath-study-refuse.mp4", 5.0, 0.32, 0.50, 1.00, "Cow-path study, the refusal: the cow on the bank above the trout"),
    ("films/cowpath-study-shadow.mp4", 6.0, 0.40, 0.55, 0.90, "Cow-path study, the shadow: cows at the gate at dusk"),
    ("films/cowpath-act1.mp4", 22.0, 0.50, 0.50, 1.00, "Cow-path cartoon, act one: the hill and the pale path the cows wore"),
    ("films/cowpath-act-desk.mp4", 18.0, 0.50, 0.52, 0.80, "Cow-path cartoon, the desk: the drawing of the cow"),
]
assert len(REELS) == 53, len(REELS)
N_REELS = len(REELS)
FRAME_SIZE = (320, 180)

# names the board uses
REEL_FIRST = 0                  # the first can the lead dog brings up (S3, 70.0)
REEL_HALF = 1                   # the one-sided one with the loop (S3, 75.5)
REEL_LEAD = 12                  # the lead dog's finished reel (S5/S6): class film 10, which the person refuses
REEL_TEETH = 17                 # class film 10 as the child drew it: the wobbly teeth (S6, thrown on the door at 177)
REEL_COW = 51                   # the cow-path one the sheepdog holds up to the lead cow (S6, 159.8): a hill, a pale path
REEL_RETRIEVER = 17             # the wooden retriever's reel after it is changed


def _slug(n):
    f = REELS[n][0]
    return f.replace(".mp4", "").replace("/", "-")


def frame_path(n):
    return FRAMES / f"{n + 1:02d}_{_slug(n)}.jpg"


def build_frames(force=False, which=None):
    """Cut one frame for every reel out of the real films with ffmpeg and cache it small (320x180 JPEG) under
    films/swarm/dogs/frames/. Only decodes; nothing else touches the films."""
    FRAMES.mkdir(parents=True, exist_ok=True)
    made = 0
    for n in (range(N_REELS) if which is None else which):
        out = frame_path(n)
        if out.exists() and not force:
            continue
        f, t = REELS[n][0], REELS[n][1]
        src = PROJECT / "assets" / f
        if not src.exists():
            raise FileNotFoundError(f"reel {n}: {src} is not there, and its frame is not cached")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                        "-vf", f"scale={FRAME_SIZE[0]}:{FRAME_SIZE[1]}:flags=lanczos", "-q:v", "3", str(out)], check=True)
        made += 1
    return made


@lru_cache(maxsize=None)
def frame(n):
    """The real frame reel n holds: an RGB image, 320x180. n counts from 0 in the order of WHAT_WE_MADE.md."""
    n = int(n) % N_REELS
    p = frame_path(n)
    if not p.exists():
        build_frames(which=[n])
    return Image.open(p).convert("RGB")


@lru_cache(maxsize=1024)
def _face(n, d):
    """The round face: a square of the frame, d px across."""
    im = frame(n)
    _, _, cx, cy, zoom, _ = REELS[int(n) % N_REELS]
    w, h = im.size
    side = h * zoom
    x0 = clamp(cx * w - side / 2, 0, w - side)
    y0 = clamp(cy * h - side / 2, 0, h - side)
    return im.crop((int(x0), int(y0), int(x0 + side), int(y0 + side))).resize((d, d), Image.LANCZOS)


def reel_title(n):
    return REELS[int(n) % N_REELS][5]


# ----------------------------------------------------------------- drawing ---
def _img(target):
    return target.img if hasattr(target, "img") else target


def _refresh(target):
    if hasattr(target, "img") and hasattr(target, "d"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


def _put(target, spr, x, y, alpha=1.0):
    """Lay an RGBA sprite on the picture with its top-left at (x, y)."""
    img = _img(target)
    x, y = int(round(x)), int(round(y))
    if alpha < 1:
        spr = spr.copy()
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * clamp(alpha))))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.width, x + spr.width), min(img.height, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return
    spr = spr.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    if img.mode == "RGBA":
        img.alpha_composite(spr, (x0, y0))
    else:
        img.paste(spr, (x0, y0), spr)
    _refresh(target)


def _tinted(spr, tint, amount):
    if not tint or amount <= 0:
        return spr
    a = spr.getchannel("A")
    out = Image.blend(spr.convert("RGB"), Image.new("RGB", spr.size, tuple(tint[:3])), clamp(amount)).convert("RGBA")
    out.putalpha(a)
    return out


class _Sheet:
    """A small supersampled sheet of tracing paper centred on a screen point. Draw on it in screen pixels
    relative to that point (x right, y down), then lay() it on the picture."""

    def __init__(self, cx, cy, half_w, half_h=None, ss=3):
        half_h = half_w if half_h is None else half_h
        self.ss = ss
        self.hw, self.hh = int(math.ceil(half_w)) + 2, int(math.ceil(half_h)) + 2
        self.x0, self.y0 = math.floor(cx) - self.hw, math.floor(cy) - self.hh
        self.fx, self.fy = cx - math.floor(cx), cy - math.floor(cy)
        self.im = Image.new("RGBA", (self.hw * 2 * ss, self.hh * 2 * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def p(self, x, y):
        return ((x + self.hw + self.fx) * self.ss, (y + self.hh + self.fy) * self.ss)

    def pts(self, pts):
        return [self.p(x, y) for x, y in pts]

    def w(self, px):
        return max(1, int(round(px * self.ss)))

    def ell(self, x, y, rx, ry=None, fill=None, outline=None, width=0.0):
        ry = rx if ry is None else ry
        (ax, ay), (bx, by) = self.p(x - rx, y - ry), self.p(x + rx, y + ry)
        if bx - ax < 1 or by - ay < 1:
            return
        self.d.ellipse([ax, ay, bx, by], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def poly(self, pts, fill=None, outline=None, width=1.0):
        q = self.pts(pts)
        if fill is not None:
            self.d.polygon(q, fill=fill)
        if outline is not None:
            self.d.line(q + q[:1], fill=outline, width=self.w(width), joint="curve")

    def line(self, pts, fill, width=1.0):
        q = self.pts(pts)
        self.d.line(q, fill=fill, width=self.w(width), joint="curve")
        r = self.w(width) / 2
        if r >= 1.5:
            for x, y in (q[0], q[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def rotate(self, degrees):
        if abs(degrees) > 0.01:
            c = self.p(0, 0)
            self.im = self.im.rotate(degrees, resample=Image.BICUBIC, center=c)
            self.d = ImageDraw.Draw(self.im, "RGBA")

    def squash(self, ky):
        """Foreshorten the whole sheet vertically about the centre line (a rigid plane tipping away)."""
        if ky >= 0.999:
            return
        w, h = self.im.size
        nh = max(1, int(round(h * ky)))
        small = self.im.resize((w, nh), Image.LANCZOS)
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cy = self.p(0, 0)[1]
        self.im.paste(small, (0, int(round(cy - cy * ky))))
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def image(self, tint=None, tint_amount=0.0):
        out = self.im.resize((self.hw * 2, self.hh * 2), Image.LANCZOS)
        return _tinted(out, tint, tint_amount)

    def lay(self, target, alpha=1.0, tint=None, tint_amount=0.0):
        if alpha <= 0:
            return
        _put(target, self.image(tint, tint_amount), self.x0, self.y0, alpha)


def _grip(im, top):
    """Cut a sprite so its grip is the middle of its top edge (where dog.draw_dog puts the mouth)."""
    box = im.getbbox() or (0, 0, im.width, im.height)
    return im.crop((0, max(0, int(top)), im.width, max(int(top) + 1, box[3] + 1)))


def _rgba(c, a=255):
    return tuple(c[:3]) + (int(clamp(a, 0, 255)),)


def _rot(x, y, a):
    ca, sa = math.cos(a), math.sin(a)
    return (x * ca - y * sa, x * sa + y * ca)


@lru_cache(maxsize=8)
def _radial(n=128):
    im = Image.new("L", (n, n), 0)
    px = im.load()
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - c, y - c) / c
            px[x, y] = int(255 * clamp(1 - r) ** 2.2)
    return im


def glow(target, x, y, r, color=AMBER, level=1.0):
    """Light added to the picture round a point (a lantern, the lamp): it brightens what is already there and
    never greys it. Draw it after the thing it lights and before the thing that gives the light."""
    if level <= 0 or r < 2:
        return
    img = _img(target)
    x0, y0, x1, y1 = int(x - r), int(y - r), int(x + r), int(y + r)
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    m = _radial().resize((x1 - x0, y1 - y0), Image.BILINEAR).crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    m = m.point(lambda v: int(v * clamp(level)))
    reg = img.crop((cx0, cy0, cx1, cy1)).convert("RGB")
    lit = ImageChops.screen(reg, Image.new("RGB", reg.size, tuple(color[:3])))
    img.paste(Image.composite(lit, reg, m), (cx0, cy0))
    _refresh(target)


# -------------------------------------------------------------- paw print ---
def _paw(sh, x, y, s, angle, color, alpha):
    a = math.radians(angle)
    c = _rgba(color, alpha)

    def P(px, py):
        qx, qy = _rot(px * s, py * s, a)
        return (x + qx, y + qy)

    pad = [(-5.2, 1.5), (-3.2, -2.6), (0, -3.8), (3.2, -2.6), (5.2, 1.5), (3.6, 5.0), (1.2, 4.0), (-1.2, 4.0), (-3.6, 5.0)]
    sh.poly([P(*p) for p in pad], fill=c)
    for tx, ty, rr in ((-6.0, -5.6, 2.0), (-2.3, -8.8, 2.2), (2.3, -8.8, 2.2), (6.0, -5.6, 2.0)):
        q = P(tx, ty)
        sh.ell(q[0], q[1], rr * s, rr * s * 1.15, fill=c)


def paw_print(ink, x, y, s=1.0, angle=0.0, wet=1.0, color=None, alpha=1.0, tint=None, tint_amount=0.0):
    """One thing written: a paw print, pad and four toes, about 15 px across at s=1, toes pointing up at angle 0
    (degrees, clockwise). wet 1 = just pressed (dark, with a shine); 0 = dried to a pale mark that stays."""
    col = color or mix_color((150, 128, 104), (62, 54, 60), wet)
    sh = _Sheet(x, y, 14 * s + 3)
    _paw(sh, 0, 0, s, angle, col, 235 * (0.55 + 0.45 * wet))
    if wet > 0.3:
        gx, gy = _rot(-1.6 * s, -0.4 * s, math.radians(angle))
        sh.ell(gx, gy, 1.5 * s, 0.9 * s, fill=_rgba((236, 244, 246), 150 * wet))
    sh.lay(ink, alpha, tint, tint_amount)
    return (x, y)


# -------------------------------------------------------------------- reel ---
def _reel_sheet(n, x, y, s, tilt, wet, paw, half, loop, tail, sway, lit, face):
    R = 24.0 * s
    tilt = clamp(tilt, 0.12, 1.0)
    ry = R * tilt
    th = 9.0 * s * math.sqrt(max(0.0, 1 - tilt * tilt))
    ext = R + 6 + max(tail * 22 * s, loop * 30 * s if half else 0)
    sh = _Sheet(x, y, ext, ext)
    lw = max(0.9, 1.25 * s ** 0.6)
    metal = mix_color(METAL, (150, 170, 184), wet * 0.45)
    edge = _rgba((40, 34, 46))
    # the leader of film that hangs out of it
    if tail > 0 and not half:
        a0 = -0.9
        bx, by = R * math.cos(a0), ry * math.sin(a0)
        L = tail * 20 * s
        pts = [(bx, by)]
        for k in range(1, 7):
            f = k / 6
            pts.append((bx + L * f * (0.75 + 0.5 * sway), by - L * f * 0.55 + L * 0.5 * f * f + 2 * s * math.sin(f * 5 + sway * 3)))
        sh.line(pts, _rgba(FILM), 4.2 * s)
        for k in range(1, 6):
            px, py = lerp(pts[k][0], pts[k + 1][0], 0.5), lerp(pts[k][1], pts[k + 1][1], 0.5)
            sh.ell(px, py, 0.7 * s, fill=_rgba((210, 200, 180), 220))
    if half and loop > 0:
        # a one-sided reel: the film has come off in a loose loop
        L = loop * 26 * s
        pts = []
        for k in range(25):
            a = k / 24 * TAU
            pts.append((R * 0.55 + L * 0.5 * (1 - math.cos(a)) * (1 + 0.25 * sway), ry * 0.3 + L * 0.42 * math.sin(a) + L * 0.25 * (1 - math.cos(a))))
        sh.line(pts, _rgba(FILM), 3.6 * s)
        sh.line(pts, _rgba((92, 84, 96)), 1.0 * s)
    # the can's wall, seen when it tips away
    if th > 0.4:
        sh.ell(0, th, R, ry, fill=_rgba(METAL_DARK), outline=edge, width=lw)
        sh.poly([(-R, 0), (R, 0), (R, th), (-R, th)], fill=_rgba(METAL_DARK))
        sh.line([(-R, 0), (-R, th)], edge, lw)
        sh.line([(R, 0), (R, th)], edge, lw)
        sh.line([(-R * 0.96, th * 0.5), (R * 0.96, th * 0.5)], _rgba((70, 76, 94), 150), max(0.8, 0.8 * s))
    sh.ell(0, 0, R, ry, fill=_rgba(metal), outline=edge, width=lw)
    if half:
        # the back flange, the film wound on it, the hub
        for k, f in enumerate((0.86, 0.74, 0.62, 0.50, 0.38)):
            sh.ell(0, 0, R * f, ry * f, fill=_rgba(FILM if k % 2 == 0 else (66, 60, 72)))
        sh.ell(0, 0, R * 0.26, ry * 0.26, fill=_rgba(metal), outline=edge, width=lw * 0.8)
        sh.ell(0, 0, R * 0.08, ry * 0.08, fill=edge)
    else:
        sh.ell(0, 0, R * 0.87, ry * 0.87, fill=_rgba(FILM))
        if face:
            d = max(4, int(2 * R * 0.79 * sh.ss))
            dh = max(2, int(d * tilt))
            pic = _face(n, d).resize((d, dh), Image.LANCZOS)
            if lit != 1.0:
                pic = Image.blend(Image.new("RGB", pic.size, (26, 24, 40)), pic, clamp(lit))
            m = Image.new("L", (d * 2, dh * 2), 0)
            ImageDraw.Draw(m).ellipse([0, 0, d * 2 - 1, dh * 2 - 1], fill=255)
            m = m.resize((d, dh), Image.LANCZOS)
            cx, cy = sh.p(0, 0)
            sh.im.paste(pic, (int(round(cx - d / 2)), int(round(cy - dh / 2))), m)
            sh.d = ImageDraw.Draw(sh.im, "RGBA")
            sh.ell(0, 0, R * 0.79, ry * 0.79, outline=_rgba((30, 26, 36)), width=max(0.8, 0.8 * s))
        else:
            sh.ell(0, 0, R * 0.79, ry * 0.79, fill=_rgba((120, 128, 140)))
    # the lamp on the rim
    (ax, ay), (bx, by) = sh.p(-R * 0.94, -ry * 0.94), sh.p(R * 0.94, ry * 0.94)
    sh.d.arc([ax, ay, bx, by], 200, 255, fill=_rgba((255, 255, 250), 210), width=sh.w(max(1.0, 1.3 * s)))
    if paw:
        _paw(sh, R * 0.34 + 0.7 * s, ry * 0.36 + 0.7 * s, 0.66 * s, 18, (24, 20, 30), 200)      # a muddy print, pale on the lid
        _paw(sh, R * 0.34, ry * 0.36, 0.66 * s, 18, (226, 212, 184), 245)
    if wet > 0:
        rs = random.Random(int(n) * 13 + 5)
        for _ in range(int(2 + 3 * wet)):
            a, f = rs.uniform(0, TAU), rs.uniform(0.3, 0.92)
            sh.ell(R * f * math.cos(a), ry * f * math.sin(a), 1.0 * s, 0.7 * s, fill=_rgba((236, 248, 250), 130 * wet))
    return sh


def reel(ink, n, x, y, s=1.0, tilt=1.0, angle=0.0, wet=0.0, paw=False, half=False, loop=1.0, tail=0.0, sway=0.0,
         lit=1.0, face=True, alpha=1.0, tint=None, tint_amount=0.0):
    """A film can, centred at (x, y); its lid is 48 px across at s=1 and shows ONE frame of the real film it
    holds (reel n of REELS, n from 0). tilt 1 = the lid faces us; 0.3 = lying nearly flat on the sill, the wall of
    the can showing below the lid. angle in degrees. wet 0..1 = drops on it. paw=True = a paw print on the lid.
    half=True = the half-made one: one side only, film wound on it and a loose loop hanging out (loop 0..1).
    tail 0..1 = a leader of film hanging out (sway moves it). lit < 1 dims the picture (out of the lamp).
    face=False leaves the lid bare. Returns the centre."""
    sh = _reel_sheet(n, x, y, s, tilt, wet, paw, half, loop, tail, sway, lit, face)
    sh.rotate(-angle)
    sh.lay(ink, alpha, tint, tint_amount)
    return (x, y)


def reel_sprite(n, s=1.0, tilt=1.0, angle=0.0, **kw):
    """The reel as an RGBA image for dog.draw_dog(carry=...): gripped by the top of its rim. kw as reel()."""
    R = 24.0 * s
    sh = _reel_sheet(n, 0, 0, s, tilt, kw.get("wet", 0.0), kw.get("paw", False), kw.get("half", False), kw.get("loop", 1.0),
                     kw.get("tail", 0.0), kw.get("sway", 0.0), kw.get("lit", 1.0), kw.get("face", True))
    sh.rotate(-angle)
    im = sh.image(kw.get("tint"), kw.get("tint_amount", 0.0))
    top = int(sh.hh - R * clamp(tilt, 0.12, 1.0) + 3 * s)
    return _grip(im, top)


def reel_stack(ink, ns, x, y, s=1.0, lean=0.0, seed=0, wet=0.0, paws=(), top_tilt=None, lit=1.0, alpha=1.0,
               tint=None, tint_amount=0.0):
    """Cans stacked on the sill. ns = the reel numbers, bottom first; (x, y) = where the bottom can's wall meets
    the board. Each can lies nearly flat; the stack leans by `lean` px per can and is never tidy; the top one is
    tipped toward us (top_tilt, default 0.62) so the frame on its lid shows. paws = the reel numbers that carry a
    paw print. Returns [(x, y, n)] can centres, bottom first."""
    rs = random.Random(seed * 131 + 7)
    out = []
    step = 9.5 * s
    cx, cy = x, y - 9.0 * s * math.sqrt(1 - 0.34 ** 2)
    for k, n in enumerate(ns):
        top = k == len(ns) - 1
        tl = (0.62 if top_tilt is None else top_tilt) if top else 0.34
        dx = lean * k + rs.uniform(-2.2, 2.2) * s
        py = cy - step * k - (R_UP * s * (tl - 0.34) if top else 0)
        reel(ink, n, cx + dx, py, s, tilt=tl, angle=rs.uniform(-5, 5) + (lean * 1.2 if top else 0), wet=wet, paw=n in paws,
             lit=lit, alpha=alpha, tint=tint, tint_amount=tint_amount)
        out.append((cx + dx, py, n))
    return out


R_UP = 14.0     # how far the tipped top can rides up

_PILE_SHAPES = (9, 12, 7, 11, 8, 6)     # six leaning piles of unequal height: 53 cans


def reel_piles(ink, x0, x1, y, count=53, s=0.42, seed=0, first=0, paws=11, lit=1.0, wet=0.0, alpha=1.0):
    """The reels stacked on the sill in the last shot: `count` cans (53 when all are up) in six leaning piles of
    unequal height between x0 and x1, bottoms on y. Cans go on in the order of REELS starting at reel `first`,
    one pile getting a can, then another, never in a tidy rotation; calling it with a growing count grows the
    same piles. `paws` of them (the last laid) carry a paw print on the lid. Returns [(x, y, n)] for every can."""
    assert 0 <= count <= sum(_PILE_SHAPES), count
    rs = random.Random(seed * 17 + 3)
    order = []
    left = list(_PILE_SHAPES)
    while sum(left):
        k = rs.choice([i for i, v in enumerate(left) for _ in range(v)])
        order.append(k)
        left[k] -= 1
    piles = [[] for _ in _PILE_SHAPES]
    for i in range(count):
        piles[order[i]].append((first + i) % N_REELS)
    pawed = set((first + i) % N_REELS for i in range(max(0, count - paws), count)) if paws else set()
    gap = (x1 - x0) / len(piles)
    out = []
    for k in (1, 3, 5, 0, 2, 4):                               # the back row first, so the front piles overlap it
        if not piles[k]:
            continue
        px = x0 + gap * (k + 0.5) + rs.uniform(-0.12, 0.12) * gap
        py = y - (5.0 * s if k % 2 else 0)
        out += reel_stack(ink, piles[k], px, py, s, lean=(-1.0, 0.8, -0.5, 1.1, 0.4, -0.8)[k] * s * 1.6, seed=seed + k, wet=wet,
                          paws=pawed, lit=lit, alpha=alpha)
    assert len(out) == count
    return out


def film_strip(ink, n, a, b, sag=10.0, s=1.0, lit=0.0, alpha=1.0):
    """A length of film pulled out of reel n, from point a to point b, hanging with `sag` px of slack. Each frame
    on it is the colour of the real frame; lit 0..1 = the lamp shining through it."""
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    half = math.hypot(b[0] - a[0], b[1] - a[1]) / 2 + abs(sag) + 8 * s
    sh = _Sheet(cx, cy, half, half)
    pts = []
    for k in range(17):
        f = k / 16
        pts.append((lerp(a[0], b[0], f) - cx, lerp(a[1], b[1], f) - cy + sag * 4 * f * (1 - f)))
    wd = 7.0 * s
    sh.line(pts, _rgba(FILM), wd)
    tiny = frame(n).resize((4, 2), Image.BILINEAR)
    cols = [tiny.getpixel((i % 4, i // 4)) for i in range(8)]
    for k in range(16):
        p, q = pts[k], pts[k + 1]
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) + 1e-6
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        hw, hh = L * 0.36, wd * 0.27
        col = mix_color(mix_color(cols[k % 8], (60, 50, 60), 0.35), mix_color(cols[k % 8], (255, 236, 190), 0.35), lit)
        sh.poly([(mx - ux * hw - nx * hh, my - uy * hw - ny * hh), (mx + ux * hw - nx * hh, my + uy * hw - ny * hh),
                 (mx + ux * hw + nx * hh, my + uy * hw + ny * hh), (mx - ux * hw + nx * hh, my - uy * hw + ny * hh)], fill=_rgba(col))
        if s >= 0.9:
            for sgn in (-1, 1):
                sh.ell(mx + nx * wd * 0.4 * sgn, my + ny * wd * 0.4 * sgn, 0.6 * s, fill=_rgba((214, 204, 186), 220))
    sh.lay(ink, alpha)
    return pts[8][0] + cx, pts[8][1] + cy


def thrown_frame(ink, n, box, level=1.0, color=(255, 214, 150), soft=2.0, image=None):
    """The lamp throwing the frame of reel n onto the door planks: light, not a picture stuck on. box = (x0, y0,
    x1, y1) on the door; the frame keeps its 16:9 inside it. The planks show through. level 0..1 fades it in.
    image = your own RGB image to throw instead (the tidy wrong drawing, say). Returns the lit rectangle."""
    if level <= 0:
        return None
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    w = min(bw, bh * 16 / 9)
    h = w * 9 / 16
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = int(w), int(h)
    src = (image or frame(n)).convert("RGB")
    if sum(src.resize((1, 1), Image.BILINEAR).getpixel((0, 0))) > 480:      # a pencilled page: thicken the pencil so it carries
        src = src.filter(ImageFilter.MinFilter(3)).point(lambda v: int(255 * (v / 255) ** 2.2))
    src = src.resize((w, h), Image.LANCZOS)
    pad = int(soft * 3) + 2
    lightmap = Image.new("RGB", (w + 2 * pad, h + 2 * pad), (0, 0, 0))
    warm = ImageChops.multiply(src, Image.new("RGB", src.size, tuple(color[:3])))
    warm = Image.blend(warm, Image.new("RGB", src.size, tuple(color[:3])), 0.16)      # even the dark parts are lit
    lightmap.paste(warm, (pad, pad))
    lightmap = lightmap.filter(ImageFilter.GaussianBlur(soft * 0.3))
    m = Image.new("L", lightmap.size, 0)
    ImageDraw.Draw(m).rectangle([pad, pad, pad + w, pad + h], fill=int(235 * clamp(level)))
    m = m.filter(ImageFilter.GaussianBlur(soft))
    img = _img(ink)
    ox, oy = int(cx - w / 2 - pad), int(cy - h / 2 - pad)
    bx0, by0, bx1, by1 = max(0, ox), max(0, oy), min(img.width, ox + lightmap.width), min(img.height, oy + lightmap.height)
    if bx1 <= bx0 or by1 <= by0:
        return None
    crop = (bx0 - ox, by0 - oy, bx1 - ox, by1 - oy)
    reg = img.crop((bx0, by0, bx1, by1)).convert("RGB")
    lit = ImageChops.screen(ImageChops.multiply(reg, Image.new("RGB", reg.size, (150, 140, 150))), lightmap.crop(crop))
    img.paste(Image.composite(lit, reg, m.crop(crop)), (bx0, by0))
    _refresh(ink)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


# -------------------------------------------------------------------- part ---
PART_KINDS = ("gear", "spool", "flange", "crank", "lens", "strip")


def _gear_pts(r, teeth, a0):
    pts = []
    for k in range(teeth * 4):
        a = a0 + k / (teeth * 4) * TAU
        rr = r * (1.0 if k % 4 in (0, 1) else 0.78)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def _part_sheet(kind, x, y, s, angle, mud, wet, weed, t, extra=0.0):
    sh = _Sheet(x, y, 26 * s + 6 + extra, 26 * s + 6 + extra)
    a = math.radians(angle)
    edge = _rgba(EDGE)
    lw = max(0.9, 1.2 * s ** 0.6)
    brass = mix_color(BRASS, (150, 132, 92), wet * 0.3)

    def R(pts):
        return [_rot(px * s, py * s, a) for px, py in pts]

    if kind == "gear":
        sh.poly(R(_gear_pts(14, 8, 0.2)), fill=_rgba(brass), outline=edge, width=lw)
        sh.ell(0, 0, 8.6 * s, fill=_rgba(BRASS_DARK, 120))
        for k in range(4):
            q = _rot(5.6 * s, 0, a + k * TAU / 4 + 0.6)
            sh.ell(q[0], q[1], 2.0 * s, fill=(0, 0, 0, 0), outline=edge, width=lw * 0.7)
            sh.ell(q[0], q[1], 1.6 * s, fill=_rgba((28, 44, 52), 200))
        sh.ell(0, 0, 2.6 * s, fill=_rgba((28, 44, 52), 230), outline=edge, width=lw * 0.7)
    elif kind == "spool":
        for sx in (-9, 9):
            sh.poly(R([(sx - 2.2, -13), (sx + 2.2, -13), (sx + 2.2, 13), (sx - 2.2, 13)]), fill=_rgba(METAL), outline=edge, width=lw)
        sh.poly(R([(-7, -4.5), (7, -4.5), (7, 4.5), (-7, 4.5)]), fill=_rgba(METAL_DARK), outline=edge, width=lw)
    elif kind == "flange":
        sh.ell(0, 0, 15 * s, fill=_rgba(METAL), outline=edge, width=lw)
        for k in range(5):
            q = _rot(9.2 * s, 0, a + k * TAU / 5)
            sh.ell(q[0], q[1], 3.3 * s, fill=_rgba((30, 46, 56), 215), outline=edge, width=lw * 0.6)
        sh.ell(0, 0, 2.4 * s, fill=_rgba((30, 46, 56), 230), outline=edge, width=lw * 0.6)
    elif kind == "crank":
        sh.line(R([(-12, 8), (4, 8), (4, -8), (12, -8)]), edge, 5.4 * s)
        sh.line(R([(-12, 8), (4, 8), (4, -8), (12, -8)]), _rgba(brass), 3.2 * s)
        sh.poly(R([(10, -12), (17, -12), (17, -4), (10, -4)]), fill=_rgba((136, 78, 50)), outline=edge, width=lw)
        q = R([(-12, 8)])[0]
        sh.ell(q[0], q[1], 4.2 * s, fill=_rgba(brass), outline=edge, width=lw)
    elif kind == "lens":
        sh.poly(R([(-13, -8), (5, -10), (5, 10), (-13, 8)]), fill=_rgba(brass), outline=edge, width=lw)
        sh.poly(R([(5, -12), (12, -12), (12, 12), (5, 12)]), fill=_rgba(BRASS_DARK), outline=edge, width=lw)
        sh.poly(R([(12, -9), (15, -7), (15, 7), (12, 9)]), fill=_rgba((170, 214, 224)), outline=edge, width=lw * 0.8)
        sh.line(R([(-9, -6.5), (2, -8)]), _rgba((255, 240, 200), 200), 1.4 * s)
    elif kind == "strip":
        pts = [(-15 + k * 2.5, 6 * math.sin(k * 0.62) - 0.12 * (k - 6) ** 2 + 3) for k in range(13)]
        sh.line(R(pts), _rgba(FILM), 6.0 * s)
        q = R(pts)
        for k in range(1, 12):
            sh.ell(q[k][0], q[k][1], 1.35 * s, 1.0 * s, fill=_rgba((120, 150, 150), 235))
    else:
        raise ValueError(f"part kind {kind!r}: one of {PART_KINDS}")
    # what the creek left on it
    rs = random.Random(hash(kind) % 997)
    for _ in range(int(3 * mud + 0.5)):                          # clods, on the underside where they hang on
        mx, my = rs.uniform(-9, 9) * s, rs.uniform(5, 11) * s
        sh.ell(mx, my, rs.uniform(2.0, 3.4) * s, rs.uniform(1.5, 2.4) * s, fill=_rgba(MUD, 235), outline=edge, width=lw * 0.5)
    if weed > 0:
        bx, by = _rot(-6 * s, 7 * s, a)
        pts = [(bx + 2.5 * s * math.sin(k * 0.9 + t * 2.2) * (k / 6), by + k * 3.6 * s * weed) for k in range(7)]
        sh.line(pts, _rgba(WEED), 2.2 * s)
        sh.line([(p[0] + 3 * s, p[1] - 4 * s) for p in pts[2:6]], _rgba((70, 132, 84)), 1.6 * s)
    if wet > 0:
        for k in range(int(2 + 3 * wet)):
            q = _rot(rs.uniform(-9, 9) * s, rs.uniform(-9, 9) * s, a)
            sh.ell(q[0], q[1], 1.2 * s, 0.9 * s, fill=_rgba((240, 250, 250), 190 * wet))
    return sh


def part(ink, x, y, s=1.0, kind="gear", angle=0.0, mud=1.0, wet=1.0, weed=1.0, t=0.0, drip=None, floor=None,
         alpha=1.0, tint=None, tint_amount=0.0):
    """A part dug out of the gravel, about 30 px across at s=1, centred at (x, y). kind: 'gear' | 'spool' |
    'flange' | 'crank' | 'lens' | 'strip'. mud 0..1 = clods of creek mud on it; weed 0..1 = a strand of weed
    hanging off it (it swings with t); wet 0..1 = shine. drip = the time it left the water: drops fall from it for
    four seconds after that, to `floor` (a y) if given. Returns the centre."""
    if drip is not None:
        drips(ink, t, x, y + 12 * s, drip, width=20 * s, floor=floor, s=s, seed=hash(kind) % 50)
    _part_sheet(kind, x, y, s, angle, mud, wet, weed, t, extra=24 * s * weed).lay(ink, alpha, tint, tint_amount)
    return (x, y)


def part_sprite(kind="gear", s=1.0, angle=0.0, mud=1.0, wet=1.0, weed=1.0, t=0.0, tint=None, tint_amount=0.0):
    """The part as an RGBA image for dog.draw_dog(carry=...), gripped at its top."""
    sh = _part_sheet(kind, 0, 0, s, angle, mud, wet, weed, t, extra=24 * s * weed)
    im = sh.image(tint, tint_amount)
    return _grip(im, int(sh.hh - 13 * s))


def drips(ink, t, x, y, t0, width=20.0, floor=None, s=1.0, life=4.0, seed=0, color=WATERDROP, heavy=1.0):
    """Water running off a thing that has just come up: drops let go along a line `width` wide at (x, y) from
    time t0, fast at first and then one at a time, gone after `life` seconds. They fall to `floor` (a y) and make
    a small tick there; without a floor they fall 70 px and fade. The thing may move: drops fall from where it is."""
    age = t - t0
    if age < 0 or age > life + 1.2:
        return
    rs = random.Random(seed * 53 + 11)
    fall = (floor - y) if floor is not None else 70.0 * s
    if fall <= 2:
        return
    sh = _Sheet(x, y + fall / 2, width / 2 + 10 * s, fall / 2 + 8 * s, ss=2)
    g = 520.0 * s
    tb = 0.0
    k = 0
    while tb < life:
        f = tb / life
        tb += (0.05 + 0.55 * f * f) / max(0.2, heavy) * rs.uniform(0.7, 1.3)
        dx = rs.uniform(-0.5, 0.5) * width
        a = age - tb
        k += 1
        if a < 0:
            continue
        hang = 0.12 + 0.2 * f                                   # it swells before it lets go
        if a < hang:
            sh.ell(dx, -fall / 2 + 1.2 * s * (a / hang), 1.1 * s, 1.1 * s + 1.6 * s * (a / hang), fill=_rgba(color, 230))
            continue
        d = 0.5 * g * (a - hang) ** 2
        if d < fall:
            ln = min(7 * s, 1.5 * s + g * (a - hang) * 0.012)
            sh.line([(dx, -fall / 2 + d - ln), (dx, -fall / 2 + d)], _rgba(color, 225), 1.5 * s)
            sh.ell(dx, -fall / 2 + d, 1.3 * s, fill=_rgba(color, 240))
        elif floor is not None:
            tk = a - hang - math.sqrt(2 * fall / g)
            if tk < 0.22:
                q = tk / 0.22
                for sgn in (-1, 1):
                    sh.line([(dx + sgn * 1.5 * s, fall / 2 - 0.5), (dx + sgn * (2 + 5 * q) * s, fall / 2 - (3.5 * math.sin(q * math.pi)) * s)],
                            _rgba(color, 220 * (1 - q)), 1.1 * s)
    sh.lay(ink)


# -------------------------------------------------------------------- page ---
_town = None


def _picture(d, name, cx, cy, size, progress, width, tidy=False, seed=3):
    """One of the children's drawings, as town.py redraws it (the same strokes the fish children hold up)."""
    global _town
    if _town is None:
        try:
            import town as _t
            _t._drawings()
            _town = _t
        except Exception:                                     # the town is not there: a plain zigzag jaw
            _town = False
    if _town:
        _town.picture(d, name, cx, cy, size, progress=progress, width=width, tidy=tidy, seed=seed, color=PENCIL)
        return
    pts = [(cx + size * (-0.4 + 0.1 * k), cy + size * (0.16 if k % 2 else -0.16)) for k in range(9)]
    n = max(2, int(len(pts) * clamp(progress)))
    d.line(pts[:n], fill=_rgba(PENCIL), width=max(1, int(width)), joint="curve")
    if progress > 0.9:
        d.rectangle([cx - size * 0.44, cy - size * 0.22, cx + size * 0.44, cy + size * 0.22], outline=_rgba(PENCIL), width=max(1, int(width)))


DRAWINGS = ("jaw", "fish_bell", "sub", "bowl_legs", "bars")


def _page_sheet(x, y, s, drawing, blank, angle, flat, wet, paw, smudge, progress, tidy, lines):
    PW, PH = 40.0 * s, 52.0 * s
    sh = _Sheet(x, y, PH * 0.72 + 4, PH * 0.72 + 4)
    paper = mix_color(PAPER, PAPER_WET, wet * 0.8)
    hw, hh = PW / 2, PH / 2
    lw = max(0.8, 1.0 * s ** 0.6)
    # a page is a stiff plane: four straight edges, always
    sh.poly([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], fill=_rgba(paper), outline=_rgba((96, 84, 80)), width=lw)
    # the ring printed on it, with its four little squares
    rc = (0.0, -hh * 0.20)
    rr = PW * 0.40
    pr = _rgba(mix_color(PRINT, paper, 0.15))
    sh.ell(rc[0], rc[1], rr, outline=pr, width=max(0.7, 0.9 * s))
    sh.ell(rc[0], rc[1], rr * 0.88, outline=pr, width=max(0.6, 0.6 * s))
    for k in range(4):
        qx, qy = rc[0] + rr * 0.94 * math.cos(k * TAU / 4), rc[1] + rr * 0.94 * math.sin(k * TAU / 4)
        q = 1.7 * s
        sh.poly([(qx - q, qy - q), (qx + q, qy - q), (qx + q, qy + q), (qx - q, qy + q)], fill=_rgba(paper), outline=pr, width=max(0.6, 0.6 * s))
    # the lines the sentence goes on
    for k in range(lines):
        ly = hh * (0.50 + 0.2 * k)
        sh.line([(-hw * 0.78, ly), (hw * 0.78, ly)], pr, max(0.6, 0.55 * s))
    if not blank:
        cx, cy = sh.p(*rc)
        _picture(sh.d, drawing, cx, cy, rr * 1.42 * sh.ss, progress, max(1.0, 0.6 * s * sh.ss), tidy=tidy)
        if progress >= 1.0 and lines:
            rs = random.Random(len(drawing) * 7 + 1)             # the child's sentence: loops, no letters
            for k in range(min(lines, 2)):
                ly = hh * (0.50 + 0.2 * k) - 1.6 * s
                end = hw * (0.7 if k == 0 else rs.uniform(-0.1, 0.4))
                pts, px = [], -hw * 0.74
                while px < end:
                    pts.append((px, ly + rs.uniform(-1.5, 1.2) * s))
                    px += rs.uniform(1.2, 2.6) * s
                if len(pts) > 1:
                    sh.line(pts, _rgba(PENCIL, 215), max(0.7, 0.75 * s))
    rs = random.Random(11)
    for _ in range(int(smudge)):
        mx, my = rs.uniform(-0.6, 0.6) * hw, rs.uniform(-0.6, 0.6) * hh
        sh.ell(mx, my, 3.4 * s, 2.7 * s, fill=_rgba((120, 150, 150), 80), outline=_rgba((96, 128, 130), 130), width=0.7)
    if paw:
        _paw(sh, hw * 0.46, hh * 0.56, 0.72 * s, 14, (70, 62, 70), 200)
    if wet > 0:
        sh.poly([(-hw, hh * 0.72), (hw, hh * 0.80), (hw, hh), (-hw, hh)], fill=_rgba((150, 176, 176), 70 * wet))
    k = 1 - 0.86 * clamp(flat)
    if k < 0.999:
        sh.squash(k)
        ey = hh * k                                             # the near edge of the sheet has a thickness
        sh.line([(-hw, ey + 0.6 * s), (hw, ey + 0.6 * s)], _rgba((150, 140, 130)), max(0.8, 1.0 * s))
    sh.rotate(-angle)
    return sh


def page(ink, x, y, s=1.0, drawing="jaw", blank=False, angle=0.0, flat=0.0, wet=0.0, paw=False, smudge=0,
         progress=1.0, tidy=False, lines=2, alpha=1.0, tint=None, tint_amount=0.0):
    """A child's page: cream paper, 40 x 52 px at s=1, centred at (x, y), with the printed ring on it and the
    child's drawing inside the ring. drawing: 'jaw' | 'fish_bell' | 'sub' | 'bowl_legs' | 'bars' (redrawn strokes,
    never the photographs). The page is a stiff plane and NEVER bends: flat 0 = it faces us, flat 1 = it lies flat
    and we see it almost edge on (carried level, or lying on the sill); angle turns it (degrees). blank=True = the
    same page with nothing drawn (the ring and the empty lines are still printed). wet 0..1, paw=True = a paw
    print in the corner, smudge = how many wet nose marks, progress < 1 = half drawn, tidy=True = the ruled-straight
    wrong version. Returns the centre."""
    _page_sheet(x, y, s, drawing, blank, angle, flat, wet, paw, smudge, progress, tidy, lines).lay(ink, alpha, tint, tint_amount)
    return (x, y)


def blank_page(ink, x, y, s=1.0, **kw):
    """A blank page: carried just as carefully. Same arguments as page()."""
    kw.pop("blank", None)
    return page(ink, x, y, s, blank=True, **kw)


def page_sprite(drawing="jaw", s=1.0, blank=False, flat=0.0, angle=0.0, wet=0.0, paw=False, smudge=0, progress=1.0,
                tidy=False, lines=2, tint=None, tint_amount=0.0):
    """The page as an RGBA image for dog.draw_dog(carry=...). The mouth holds the middle of its top edge; with
    flat near 1 it rides level under the muzzle. It does not bend, whatever the dog does."""
    sh = _page_sheet(0, 0, s, drawing, blank, angle, flat, wet, paw, smudge, progress, tidy, lines)
    im = sh.image(tint, tint_amount)
    top = int(sh.hh - 26.0 * s * (1 - 0.86 * clamp(flat)) - 1)
    return _grip(im, top)


# ----------------------------------------------------------------- lantern ---
def _lantern_sheet(x, y, s, t, lit, swing, seed=0):
    sh = _Sheet(x, y, 30 * s + 4, 46 * s + 4)
    a = math.radians(swing)
    edge = _rgba(EDGE)
    lw = max(0.9, 1.2 * s ** 0.6)

    def R(pts):                                                 # it hangs from the grip at (0, 0)
        return [_rot(px * s, py * s, a) for px, py in pts]

    # the wire bail
    bail = [(-9, 13), (-9.5, 6), (-6, 1.5), (0, 0), (6, 1.5), (9.5, 6), (9, 13)]
    sh.line(R(bail), edge, 2.2 * s)
    sh.line(R(bail), _rgba((150, 140, 120)), 1.0 * s)
    # cap, chimney
    sh.poly(R([(-3, 8), (3, 8), (4, 12), (-4, 12)]), fill=_rgba(BRASS_DARK), outline=edge, width=lw)
    sh.poly(R([(-11, 16), (-6, 11.5), (6, 11.5), (11, 16)]), fill=_rgba(BRASS), outline=edge, width=lw)
    # the glass
    fl = 0.86 + 0.14 * math.sin(t * 11.0 + seed) * math.sin(t * 4.3 + seed * 2)
    glass = mix_color((70, 92, 100), (255, 226, 150), lit * fl)
    sh.poly(R([(-8.5, 16), (8.5, 16), (9.5, 22), (9.5, 31), (8, 36), (-8, 36), (-9.5, 31), (-9.5, 22)]), fill=_rgba(glass, 240), outline=edge, width=lw)
    if lit > 0.05:
        fy = 31 - 9 * fl * lit
        sway = 1.2 * math.sin(t * 7.0 + seed)
        sh.poly(R([(-3, 32), (-2.4, 28), (sway, fy), (2.4, 28), (3, 32), (0, 33.5)]), fill=_rgba((255, 250, 226), 255 * clamp(lit * 1.4)))
        sh.poly(R([(-1.4, 32), (sway * 0.5, 28.5), (1.4, 32)]), fill=_rgba((255, 170, 70), 230 * clamp(lit * 1.4)))
    for gx in (-4.6, 4.6):                                      # the guard wires
        sh.line(R([(gx, 16), (gx * 1.1, 26), (gx, 36)]), _rgba(EDGE, 190), 0.9 * s)
    sh.line(R([(-6.5, 19), (-7.2, 27)]), _rgba((255, 255, 245), 150), 1.3 * s)
    # the font
    sh.poly(R([(-10, 36), (10, 36), (11.5, 41), (-11.5, 41)]), fill=_rgba(BRASS), outline=edge, width=lw)
    sh.poly(R([(-12.5, 41), (12.5, 41), (12.5, 43.5), (-12.5, 43.5)]), fill=_rgba(BRASS_DARK), outline=edge, width=lw)
    return sh, R([(0, 27)])[0]


def lantern(ink, x, y, s=1.0, t=0.0, lit=1.0, swing=0.0, halo=1.0, under=True, seed=0, alpha=1.0, tint=None, tint_amount=0.0):
    """A storm lantern hanging from its wire handle; (x, y) is the top of the handle (the dog's mouth), the body
    hangs 44 px below at s=1. swing = degrees off plumb. lit 0..1 (the flame flickers with t). halo 0..1 = the
    light it throws on whatever is already drawn round it (bigger and softer under water, with motes in it):
    draw the lantern AFTER the things it should light. Returns the flame's screen point."""
    sh, fl = _lantern_sheet(x, y, s, t, lit, swing, seed)
    fx, fy = x + fl[0], y + fl[1]
    if halo > 0 and lit > 0:
        fk = 0.9 + 0.1 * math.sin(t * 9.0 + seed)
        r = (150 if under else 105) * s ** 0.8
        glow(ink, fx, fy, r * fk, (255, 196, 110) if not under else (255, 214, 140), 0.62 * halo * lit)
        glow(ink, fx, fy, r * 0.42, (255, 236, 190), 0.55 * halo * lit)
        if under:
            rs = random.Random(seed + 9)
            d = getattr(ink, "d", None) or ImageDraw.Draw(_img(ink), "RGBA")
            for _ in range(16):
                a, rr, ph = rs.uniform(0, TAU), rs.uniform(0.15, 0.8) * r, rs.uniform(0, 6)
                mx, my = fx + rr * math.cos(a + 0.1 * math.sin(t * 0.7 + ph)), fy + rr * math.sin(a) - 4 * math.sin(t * 0.5 + ph)
                d.ellipse([mx - 1, my - 1, mx + 1, my + 1], fill=(255, 240, 200, int(150 * halo * lit * (1 - rr / r))))
    sh.lay(ink, alpha, tint, tint_amount)
    return (fx, fy)


def lantern_sprite(s=1.0, t=0.0, lit=1.0, swing=0.0, seed=0, tint=None, tint_amount=0.0):
    """The lantern as an RGBA image for dog.draw_dog(carry=...), held by the top of its handle. It carries no
    halo: call glow(ink, x, y, r) at the dog's mouth + (0, 27 * s) before drawing the dog."""
    sh, _ = _lantern_sheet(0, 0, s, t, lit, swing, seed)
    im = sh.image(tint, tint_amount)
    return _grip(im, sh.hh - 1)


# ------------------------------------------------------- the pile on the sill ---
# What the lead dog lays across the sill in S3, in the order it comes up (board, boundary frame 84.0), and what
# a longer pile goes on with. (kind, argument, paw print, dx, lift, angle)
PILE = [
    ("page", "jaw", True, 0, 0, -6),
    ("reel", REEL_FIRST, True, 44, 0, 4),
    ("half", REEL_HALF, False, 92, 0, -3),
    ("strip", None, False, 142, 0, 8),
    ("flange", None, False, 172, 0, -10),
    ("gear", None, False, 20, 3, 20),
    ("reel", 2, False, 68, 12, -5),
    ("spool", None, False, 120, 2, 84),
    ("page", "fish_bell", False, 150, 10, 5),
    ("reel", 3, False, 30, 22, 3),
    ("crank", None, False, 100, 20, -14),
    ("reel", 4, False, 122, 22, -2),
]


def puddle(ink, x, y, w, level=1.0, t=0.0, color=(150, 190, 200), alpha=1.0):
    """Standing water on a board: a thin flat shine `w` wide centred at (x, y), with a light edge that moves a
    little. level 0..1 = how much of it there is."""
    if level <= 0 or w < 2:
        return
    hw = w / 2 * (0.4 + 0.6 * clamp(level))
    sh = _Sheet(x, y, hw + 4, 6, ss=2)
    pts = []
    for k in range(24):
        a = k / 24 * TAU
        wob = 1 + 0.08 * math.sin(3 * a + 1.3) + 0.05 * math.sin(5 * a + t * 0.8)
        pts.append((hw * wob * math.cos(a), 2.6 * wob * math.sin(a)))
    sh.poly(pts, fill=_rgba((30, 40, 56), 95 * alpha))
    sh.poly([(px * 0.92, py * 0.75 - 0.3) for px, py in pts], fill=_rgba(color, 80 * alpha))
    sh.line([(-hw * 0.6, -1.0), (-hw * 0.1 + 2 * math.sin(t * 1.3), -1.3)], _rgba((246, 252, 250), 200 * alpha), 1.0)
    sh.line([(hw * 0.25, 0.6), (hw * 0.55, 0.4)], _rgba((246, 252, 250), 130 * alpha), 0.8)
    sh.lay(ink)


def pile(ink, t, x, y, count, s=0.6, born=None, wet=1.0, edge=None, floor=None, spread=1.0, lit=1.0, alpha=1.0):
    """The pile on the sill: small, wet, and growing. (x, y) = the board under its left end. count = how many
    things are on it (0..12): they come in the order of PILE (the child's page with a paw print, the first reel
    with a paw print, the one-sided reel with its loop, a strip, a flange, then a second row on top). born = the
    time each was laid ([t0, t1, ...]): a thing settles for a third of a second after it lands, drips for four
    seconds, and the water under the pile widens with each one. edge = the y of the sill's front lip: if given,
    water runs over it in drops, down to `floor` (the y of the water line) if that is given too. spread stretches the row. Returns [(x, y, kind)] for the things drawn."""
    count = int(clamp(count, 0, len(PILE)))
    out = []
    if count <= 0:
        return out
    born = list(born or [])
    last_x = max(PILE[k][3] for k in range(count)) * s * spread
    puddle(ink, x + last_x / 2, y + 1.5, last_x + 60 * s, level=wet * (0.45 + 0.55 * count / len(PILE)), t=t)
    for k in range(count):
        kind, arg, pw, dx, lift, ang = PILE[k]
        age = t - born[k] if k < len(born) else 99.0
        if age < 0:
            continue
        set_ = 1 - clamp(age / 0.32)
        drop = -7 * s * set_ * set_                               # it lands, and settles
        w = wet * (1.0 if age < 4 else max(0.45, 1 - (age - 4) / 20))
        px = x + dx * s * spread
        if kind == "page":
            py = y - 3.4 * s - lift * s + drop
            py = y - 6.0 * s - lift * s + drop
            page(ink, px, py, s, drawing=arg, flat=0.72, angle=ang, wet=w * 0.6, paw=pw, alpha=alpha)
        elif kind in ("reel", "half"):
            py = y - 15.5 * s - lift * s + drop
            reel(ink, arg, px, py, s, tilt=0.62, angle=ang, wet=w, paw=pw, half=kind == "half", loop=0.8, lit=lit, alpha=alpha)
        else:
            py = y - (5.0 if kind in ("strip", "crank") else 8.0) * s - lift * s + drop
            _s = _part_sheet(kind, px, py, s * 0.9, ang, 0.6, w, 0.0, t)
            if kind in ("flange", "gear"):
                _s.squash(0.55)
            _s.lay(ink, alpha)
        if age < 4.2 and edge is not None:
            drips(ink, t, px, edge, born[k] + 0.25, width=22 * s, floor=floor, s=max(0.6, s), seed=k, heavy=0.8)
        out.append((px, py, kind))
    return out


# ------------------------------------------------------------------ bubbles ---
def _bubble_on(sh, x, y, r, alpha=1.0, fill=60):
    sh.ell(x, y, r, fill=_rgba((220, 240, 232), fill * alpha), outline=_rgba((244, 252, 248), 235 * alpha), width=max(0.8, r * 0.14))
    if r > 2.2:
        sh.ell(x - r * 0.38, y - r * 0.38, r * 0.2, fill=_rgba((255, 255, 255), 235 * alpha))


def picture_bubble(ink, t, x, y, r=30.0, drawing="jaw", n=None, grow=1.0, progress=1.0, pop=0.0, tidy=False, calm=False,
                   seed=0, tail=None, alpha=1.0):
    """A bubble with a picture inside, centred at (x, y), radius r. The picture is one of the children's drawings
    (drawing: 'jaw' | 'fish_bell' | 'sub' | 'bowl_legs' | 'bars'), or, with n=<reel number>, the real frame that
    reel holds. grow 0..1 blows it up; progress 0..1 draws the drawing stroke by stroke; pop 0..1 bursts it into
    drops; calm=True holds its skin dead still (under the ice). tail = the mouth it came from: three small
    bubbles lead back to it. Returns the centre."""
    g = smooth(clamp(grow))
    if g <= 0.01 or pop >= 1:
        return (x, y)
    tt = 0.0 if calm else t
    R = r * (0.25 + 0.75 * g)
    ext = R * 1.9 + 8
    if tail is not None:
        ext = max(ext, math.hypot(tail[0] - x, tail[1] - y) + 8)
    sh = _Sheet(x, y, ext, ext)
    if tail is not None and pop < 0.3:
        tx, ty = tail[0] - x, tail[1] - y
        L = math.hypot(tx, ty) + 1e-6
        for q, f in enumerate((0.18, 0.44, 0.72)):
            if g < f * 0.8:
                continue
            ex, ey = tx * (1 - R / L), ty * (1 - R / L)            # from the mouth to the bubble's skin
            bx, by = lerp(tx, ex, f), lerp(ty, ey, f) + (0 if calm else 1.5 * math.sin(tt * 3 + q))
            _bubble_on(sh, bx, by, 1.8 + q * 1.5, alpha)
    if pop > 0:
        rs = random.Random(seed + 3)
        for q in range(14):
            a = q / 14 * TAU + rs.uniform(-0.2, 0.2)
            rr = R * (1 + pop * rs.uniform(0.3, 0.9))
            sh.ell(rr * math.cos(a), rr * math.sin(a) + 14 * pop * pop, 2.2 * (1 - pop) + 0.6, fill=_rgba((236, 250, 244), 230 * (1 - pop) * alpha))
        if pop > 0.35:
            sh.lay(ink)
            return (x, y)
    rim = []
    for q in range(48):
        a = q / 48 * TAU
        wob = 1 + 0.02 * math.sin(3 * a + tt * 2.2 + seed) + 0.012 * math.sin(5 * a - tt * 3.1)
        rim.append((R * wob * math.cos(a), R * wob * math.sin(a)))
    sh.poly(rim, fill=_rgba((234, 240, 226), 238 * (1 - pop) * alpha))
    if g > 0.55:
        cx, cy = sh.p(0, R * 0.04)
        if n is not None:
            d = max(4, int(2 * R * 0.84 * sh.ss))
            m = Image.new("L", (d, d), 0)
            ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=int(255 * alpha))
            sh.im.paste(_face(n, d), (int(cx - d / 2), int(cy - d / 2)), m)
            sh.d = ImageDraw.Draw(sh.im, "RGBA")
        else:
            _picture(sh.d, drawing, cx, cy, R * 1.34 * sh.ss, progress, max(sh.ss * 0.8, R * sh.ss * 0.036), tidy=tidy, seed=seed)
    sh.poly(rim, outline=_rgba((250, 255, 250), 255 * alpha), width=max(1.4, 1.9 * (R / 30) ** 0.5))
    (ax, ay), (bx, by) = sh.p(-R * 0.86, -R * 0.86), sh.p(R * 0.86, R * 0.86)
    sh.d.arc([ax, ay, bx, by], 20, 80, fill=_rgba((120, 170, 170), 150 * alpha), width=sh.w(1.6))
    (ax, ay), (bx, by) = sh.p(-R * 0.8, -R * 0.8), sh.p(R * 0.8, R * 0.8)
    sh.d.arc([ax, ay, bx, by], 200, 262, fill=_rgba((255, 255, 255), 235 * alpha), width=sh.w(2.4))
    sh.ell(-R * 0.58, -R * 0.26, R * 0.045, fill=_rgba((255, 255, 255), 235 * alpha))
    sh.lay(ink)
    return (x, y)


@lru_cache(maxsize=256)
def _breath_plan(dur, seed, heavy):
    """When each breath bubble leaves the muzzle: [(time since t0, air left then, size, side wobble phase)]."""
    rs = random.Random(seed * 91 + 17)
    out = []
    tb = 0.0
    last_gap = max(0.9, min(1.6, dur * 0.22))
    while tb < dur - last_gap - 0.4:
        air = 1 - tb / dur
        for _ in range(1 + (rs.random() < air * 0.8) + (rs.random() < air * 0.5 * heavy)):
            out.append((tb + rs.uniform(0, 0.06), air, rs.uniform(0.7, 1.15), rs.uniform(0, 6.28)))
        tb += (0.16 + 0.9 * (1 - air) ** 2) * rs.uniform(0.75, 1.25) / heavy
    out.append((dur, 0.0, 0.8, rs.uniform(0, 6.28)))               # the last one, alone
    return tuple(out)


def breath_left(t, t0, t_out):
    """How much air a dog that went under at t0 and runs out at t_out has: 1 .. 0."""
    return 1 - ramp(t, t0, t_out)


def breath(ink, t, x, y, t0, t_out, s=1.0, seed=0, facing=1, ceiling=None, release=None, surface=None, heavy=1.0,
           alpha=1.0, at=None):
    """Breath bubbles that run out. They leave the muzzle at (x, y) from time t0: at first in twos and threes,
    big; then one at a time, smaller, further apart; then a long wait; then, at t_out, one last small bubble,
    alone. After that there are none: the dog has to go up. Each rises with a wobble and swells a little.
    ceiling = the y of the underside of the ice: bubbles stop there, flatten and stay (until `release`, the time
    the ice breaks, when they all go up at once). surface = the y of the line: bubbles end there with a small
    ring. at = a function time -> (x, y) if the muzzle moves and bubbles should start where it WAS. heavy > 1 =
    a big dog. Returns the air left, 1 .. 0."""
    air = breath_left(t, t0, t_out)
    if t < t0:
        return air
    plan = _breath_plan(round(t_out - t0, 2), seed, heavy)
    top = min(v for v in (ceiling, surface, y - 520) if v is not None)
    live = []
    for tb, a0, sz, ph in plan:
        age = t - t0 - tb
        if age < 0:
            continue
        bx0, by0 = at(t0 + tb) if at else (x, y)
        r = s * (1.3 + 4.6 * a0 ** 0.8) * sz
        v = (34 + 7.0 * r / s) * s
        rise = v * age + 14 * s * (1 - math.exp(-age * 3))
        bx = bx0 + facing * 7 * s * (1 - math.exp(-age * 2.5)) + 3.2 * s * math.sin(age * 4.4 + ph) * min(1, age * 2)
        by = by0 - rise
        rr = r * (1 + 0.1 * min(age, 3))
        if ceiling is not None and by - rr * 0.5 <= ceiling:
            if release is not None and t >= release:
                by = ceiling + rr * 0.5 - (v * 1.6) * (t - release)
                if by < ceiling - 40:
                    continue
                live.append((bx, by, rr, rr, 1.0))
            else:
                held = age - (by0 - ceiling) / v
                sl = math.sin(ph * 3 + t * 0.4) * 2 * s
                live.append((bx + sl, ceiling + rr * 0.42, rr * (1.35 + 0.1 * min(held, 2)), rr * 0.5, 1.0))
            continue
        if surface is not None and by - rr <= surface:
            tk = (surface - (by - rr)) / v
            if tk < 0.25:
                live.append((bx, surface, rr * (1 + 3 * tk / 0.25), 0.9, -(1 - tk / 0.25)))
            continue
        if by < top - 10:
            continue
        live.append((bx, by, rr, rr, 1.0))
    if not live:
        return air
    x0, x1 = min(b[0] - b[2] for b in live) - 3, max(b[0] + b[2] for b in live) + 3
    y0, y1 = min(b[1] - b[3] for b in live) - 3, max(b[1] + b[3] for b in live) + 3
    sh = _Sheet((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, ss=2 if (x1 - x0) * (y1 - y0) > 60000 else 3)
    ox, oy = (x0 + x1) / 2, (y0 + y1) / 2
    for bx, by, rx, ry, kind in live:
        if kind < 0:                                              # a ring where one ends at the line
            sh.ell(bx - ox, by - oy, rx, ry, outline=_rgba((240, 252, 248), 220 * -kind * alpha), width=1.0)
            continue
        sh.ell(bx - ox, by - oy, rx, ry, fill=_rgba((214, 238, 234), 56 * alpha), outline=_rgba(BUBBLE, 235 * alpha), width=max(0.8, min(rx, ry) * 0.2))
        if rx > 2.2 * s:
            sh.ell(bx - ox - rx * 0.36, by - oy - ry * 0.36, rx * 0.2, ry * 0.2, fill=_rgba((255, 255, 255), 235 * alpha))
    sh.lay(ink)
    return air


# ---------------------------------------------------------------------- ice ---
@lru_cache(maxsize=16)
def _ice_plan(x0, x1, seed):
    rs = random.Random(seed * 29 + 5)
    cuts = [x0]
    x = x0
    while x < x1 - 60:
        x += rs.uniform(46, 120)
        cuts.append(min(x, x1))
    if cuts[-1] < x1:
        cuts.append(x1)
    plates = []
    for a, b in zip(cuts, cuts[1:]):
        plates.append((a, b, rs.uniform(-1, 1), rs.uniform(0.6, 1.3), rs.uniform(-6, 6), rs.uniform(0, 0.25)))
    marks = [(rs.uniform(x0, x1), rs.uniform(0.2, 0.8), rs.uniform(1.0, 3.2)) for _ in range(int((x1 - x0) / 9))]
    return tuple(plates), tuple(marks)


def ice_sheet(ink, t, x0, x1, y, thick=12.0, freeze=1.0, crack=0.0, breakup=0.0, stamps=(), hooves=(), origin=None,
              view="below", seed=0, alpha=1.0):
    """A sheet of ice lying on the water from x0 to x1 with its top on the line y; `thick` px deep.
    freeze 0..1 = it grows from `origin` (an x; default x0) outward with a feathered edge, as fast as you run it.
    hooves = [(x, weight 0..1)]: where the lead cow stands on it; from below each is a dark shape pressed on the
    sheet. stamps = [(x, p 0..1)]: a hoof coming down hard: a white star in the ice, bursting open over p.
    crack 0..1 = the crack runs out from the first stamp both ways and splits the sheet into plates.
    breakup 0..1 = the plates tip, drift apart, sink and are gone. view 'below' (we are under it: pale underside,
    trapped air, soft light) or 'side' (level with the line: a white slab with a bright top).
    Nothing boils in it: under the ice everything is still. Returns the y of its underside."""
    if freeze <= 0 or breakup >= 1 or x1 <= x0:
        return y + thick
    plates, marks = _ice_plan(int(x0), int(x1), seed)
    org = x0 if origin is None else origin
    reach = smooth(clamp(freeze)) * max(org - x0, x1 - org) * 1.04
    fx0, fx1 = max(x0, org - reach), min(x1, org + reach)
    sx = stamps[0][0] if stamps else (x0 + x1) / 2
    crk = clamp(crack) * max(sx - x0, x1 - sx)
    b = smooth(clamp(breakup))
    sh = _Sheet((x0 + x1) / 2, y + thick / 2, (x1 - x0) / 2 + 6, thick / 2 + 46, ss=2)
    ox, oy = (x0 + x1) / 2, y + thick / 2
    below = view == "below"
    body = (206, 232, 238) if below else (232, 244, 248)
    for a_, b_, sgn, wgt, dx, dly in plates:
        pa, pb = max(a_, fx0), min(b_, fx1)
        if pb - pa < 2:
            continue
        bb = clamp((b - dly) / (1 - dly)) if b > 0 else 0.0
        if bb >= 1:
            continue
        mid = (pa + pb) / 2
        ang = sgn * 0.5 * bb
        sink = 40 * bb * bb * wgt
        gap = (1.5 if (crk > 0 and abs(mid - sx) - (pb - pa) / 2 < crk) else 0) + 5 * bb
        al = 235 * (1 - bb ** 1.5) * alpha * (0.9 if below else 1)

        def T(px, py, mid=mid, ang=ang, sink=sink, dx=dx, bb=bb):
            qx, qy = _rot(px - mid, py - thick / 2, ang)
            return (mid + qx + dx * bb - ox, y + thick / 2 + qy + sink - oy)

        # the growing edge is feathered: needles of frost run ahead of the sheet
        left, right = pa + gap / 2, pb - gap / 2
        top = [(left, 0), (right, 0)]
        bot = []
        nseg = max(2, int((right - left) / 14))
        for k in range(nseg + 1):
            px = lerp(right, left, k / nseg)
            bot.append((px, thick * (0.82 + 0.18 * math.sin(px * 0.21 + seed) * math.sin(px * 0.057))))
        sh.poly([T(*p) for p in top + bot], fill=_rgba(body, al))
        sh.line([T(left, 0.8), T(right, 0.8)], _rgba((255, 255, 255), min(255, al * 1.1)), 1.8 if not below else 1.2)
        sh.line([T(*p) for p in bot], _rgba(ICE_BLUE if below else (170, 206, 222), al), 1.2)
        for mx, f, r in marks:                                     # air caught in it
            if left + 3 < mx < right - 3:
                q = T(mx, thick * f)
                sh.ell(q[0], q[1], r * 0.8, r * 0.5, fill=_rgba((255, 255, 255), al * 0.55))
    if freeze < 1 and b <= 0:
        rs = random.Random(seed + 77)
        for ex, sgn in ((fx0, -1), (fx1, 1)):
            if (sgn < 0 and ex <= x0 + 1) or (sgn > 0 and ex >= x1 - 1):
                continue
            for k in range(7):
                L = rs.uniform(8, 30)
                yy = thick * rs.uniform(0.05, 0.8)
                sh.line([(ex - ox, y + yy - oy), (ex + sgn * L - ox, y + yy * 0.8 + rs.uniform(-2, 2) - oy)], _rgba((240, 250, 252), 220 * alpha), 1.1)
                sh.line([(ex + sgn * L * 0.5 - ox, y + yy * 0.9 - oy), (ex + sgn * L * 0.75 - ox, y + yy * 0.9 + 4 - oy)], _rgba((240, 250, 252), 170 * alpha), 0.8)
    if b < 0.5:
        k = 1 - b * 2
        for hx, wt in hooves:                                      # her weight on it, seen through it
            if fx0 < hx < fx1:
                if below:
                    sh.ell(hx - ox, y + thick * 0.2 - oy, 11, thick * 0.34, fill=_rgba((40, 52, 70), 165 * wt * k * alpha))
                    sh.ell(hx - ox, y + thick * 0.2 - oy, 16, thick * 0.5, outline=_rgba((255, 255, 255), 90 * wt * k * alpha), width=0.8)
                else:
                    sh.ell(hx - ox, y + 2 - oy, 12, 2.2, fill=_rgba((60, 70, 90), 110 * wt * k * alpha))
        for hx, p in stamps:
            if p <= 0:
                continue
            rs = random.Random(int(hx) + seed)
            for q in range(9):
                a = q / 9 * math.pi + rs.uniform(-0.12, 0.12)
                L = (8 + 20 * smooth(p)) * rs.uniform(0.6, 1.2)
                sh.line([(hx - ox, y + 1.5 - oy), (hx + L * math.cos(a) - ox, y + 1.5 + min(thick * 0.95, L * math.sin(a) * 0.6) - oy)],
                        _rgba((255, 255, 255), 250 * k * alpha), 1.3)
            sh.ell(hx - ox, y + 2 - oy, 5 + 3 * p, 2.4, fill=_rgba((255, 255, 255), 230 * k * alpha))
        if crk > 0:
            rs = random.Random(seed + 41)
            for sgn in (-1, 1):
                pts, px = [(sx, y + thick * 0.15)], sx
                while abs(px - sx) < crk:
                    px += sgn * rs.uniform(7, 16)
                    px = clamp(px, x0, x1)
                    pts.append((px, y + thick * rs.uniform(0.12, 0.88)))
                    if px in (x0, x1):
                        break
                if len(pts) > 1:
                    sh.line([(px_ - ox, py_ - oy) for px_, py_ in pts], _rgba((255, 255, 255), 250 * k * alpha), 1.5)
                    sh.line([(px_ - ox, py_ + 1.2 - oy) for px_, py_ in pts], _rgba((60, 96, 120), 150 * k * alpha), 0.8)
    sh.lay(ink)
    return y + thick


# ------------------------------------------------------------------ sheets ---
def _ground(kind, size):
    """A piece of the film's two worlds to look at the props against: dusk boards, or creek water."""
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    if kind == "dusk":
        for yy in range(h):
            d.line([(0, yy), (w, yy)], fill=mix_color((74, 58, 110), (214, 138, 104), (yy / h) ** 1.4))
        d.rectangle([0, h - 34, w, h], fill=(128, 90, 74))
        d.line([(0, h - 34), (w, h - 34)], fill=(196, 150, 110), width=2)
        for xx in range(0, w, 46):
            d.line([(xx, h - 33), (xx, h)], fill=(96, 66, 58), width=1)
    else:
        for yy in range(h):
            d.line([(0, yy), (w, yy)], fill=mix_color((40, 128, 132), (16, 62, 74), yy / h))
        d.rectangle([0, h - 22, w, h], fill=(58, 84, 78))
        rs = random.Random(4)
        for _ in range(w // 5):
            xx, yy = rs.uniform(0, w), rs.uniform(h - 22, h)
            d.ellipse([xx - 3, yy - 2, xx + 3, yy + 2], fill=mix_color((86, 108, 96), (40, 62, 60), rs.random()))
    return im


def _sheet_main(path):
    W_, H_ = 1440, 1500
    im = Image.new("RGB", (W_, H_), (18, 16, 24))
    rows = [("dusk", 250), ("dusk", 250), ("water", 250), ("water", 250), ("dusk", 250), ("water", 250)]
    y = 0
    bands = []
    for kind, hh in rows:
        im.paste(_ground(kind, (W_, hh)), (0, y))
        bands.append((y, hh))
        y += hh
    # 1 · reels, close and at film size
    y0, hh = bands[0]
    fl = y0 + hh - 34
    reel(im, 0, 90, fl - 80, 2.6)
    reel(im, 13, 250, fl - 80, 2.6, wet=1, paw=True)
    reel(im, REEL_TEETH, 410, fl - 80, 2.6, tail=1.0)
    reel(im, 51, 570, fl - 62, 2.6, tilt=0.5, angle=-8)
    reel(im, 1, 730, fl - 70, 2.6, half=True, loop=1.0)
    reel(im, 47, 870, fl - 30, 2.6, tilt=0.3)
    for k in range(8):                                           # at film size (dog scale 0.6)
        reel(im, k * 6, 990 + k * 34, fl - 100, 0.6)
        reel(im, k * 6 + 3, 990 + k * 34, fl - 60, 0.6, tilt=0.45, paw=k % 2 == 0)
    reel_stack(im, [3, 14, 22, 30, 41], 1300, fl, 1.0, lean=1.5, paws={41})
    reel_stack(im, [5, 6, 7], 1385, fl, 0.6, lean=-1.0)
    # 2 · pages, paw prints, parts
    y0, hh = bands[1]
    fl = y0 + hh - 34
    for k, dname in enumerate(DRAWINGS):
        page(im, 80 + k * 125, fl - 90, 2.6, drawing=dname, paw=k == 0, smudge=2 if k == 3 else 0)
    blank_page(im, 705, fl - 90, 2.6)
    page(im, 840, fl - 16, 2.6, drawing="jaw", flat=0.86, paw=True, wet=0.8)
    blank_page(im, 990, fl - 16, 2.6, flat=0.86)
    page(im, 840, fl - 130, 2.6, drawing="bars", flat=0.7, angle=12)
    page(im, 990, fl - 130, 2.6, drawing="jaw", tidy=True, flat=0.3)
    for k in range(5):
        page(im, 1090 + k * 34, fl - 150, 0.6, drawing=DRAWINGS[k])
        page(im, 1090 + k * 34, fl - 110, 0.6, drawing=DRAWINGS[k], flat=0.84)
    paw_print(im, 1110, fl - 50, 2.6, angle=-12)
    paw_print(im, 1190, fl - 50, 2.6, angle=10, wet=0.0)
    for k in range(6):
        paw_print(im, 1250 + k * 26, fl - 46 - (k % 2) * 10, 0.9, angle=-14 + 6 * k, wet=1 - k / 5)
    for k in range(4):
        paw_print(im, 1250 + k * 16, fl + 12, 0.45, angle=80, wet=1)
    # 3 · parts under water, dripping above
    y0, hh = bands[2]
    fl = y0 + hh - 22
    for k, kind in enumerate(PART_KINDS):
        part(im, 80 + k * 130, y0 + 90, 2.6, kind=kind, t=0.3 * k, **UNDER)
        part(im, 60 + k * 44, fl - 16, 0.6, kind=kind, t=0.3 * k, **UNDER)
    for k, kind in enumerate(("gear", "flange", "crank")):
        part(im, 900 + k * 150, y0 + 70, 2.0, kind=kind, t=1.0 + 0.4 * k, drip=0.0 + 0.3 * k, floor=fl, angle=15 * k)
    # 4 · lanterns, bubbles
    y0, hh = bands[3]
    fl = y0 + hh - 22
    lantern(im, 110, y0 + 60, 2.6, t=0.4)
    lantern(im, 300, y0 + 80, 1.2, t=1.1, swing=14)
    lantern(im, 420, y0 + 110, 0.6, t=2.0, swing=-10)
    lantern(im, 520, y0 + 80, 1.2, t=0.2, lit=0.0)
    picture_bubble(im, 0.3, 680, y0 + 110, 70, "jaw", tail=(600, y0 + 220))
    picture_bubble(im, 0.9, 850, y0 + 100, 56, "fish_bell", progress=0.6)
    picture_bubble(im, 1.4, 990, y0 + 120, 46, "bars")
    picture_bubble(im, 1.4, 1100, y0 + 90, 30, "jaw", tidy=True)
    picture_bubble(im, 1.4, 1100, y0 + 180, 30, "sub", pop=0.25)
    picture_bubble(im, 2.0, 1200, y0 + 110, 46, n=REEL_COW)
    picture_bubble(im, 2.0, 1290, y0 + 170, 18, "jaw")
    picture_bubble(im, 2.0, 1350, y0 + 80, 30, "bowl_legs", grow=0.7)
    # 5 · the pile growing on the sill
    y0, hh = bands[4]
    fl = y0 + hh - 34
    for k, cnt in enumerate((1, 2, 3, 5, 8, 12)):
        pile(im, 10.0, 20 + k * 236, fl, cnt, s=1.2 if k < 4 else 1.0, born=[9.9 - 0.9 * (cnt - 1 - q) for q in range(cnt)], edge=fl + 6)
    for k, cnt in enumerate((1, 3, 5)):
        pile(im, 10.0, 60 + k * 240, fl - 150, cnt, s=0.6, born=[9.7 - 0.9 * (cnt - 1 - q) for q in range(cnt)])
    reel_piles(im, 780, 1080, fl - 110, 53, s=0.6)
    reel_piles(im, 1180, 1350, fl - 120, 53, s=0.42)
    # 6 · ice and breath
    y0, hh = bands[5]
    d = ImageDraw.Draw(im)
    for k, (fz, cr, br) in enumerate(((0.45, 0, 0), (1, 0, 0), (1, 0.6, 0), (1, 1, 0.55))):
        xa = 20 + k * 355
        d.rectangle([xa, y0, xa + 335, y0 + 40], fill=(88, 70, 118))
        d.line([(xa, y0 + 40), (xa + 335, y0 + 40)], fill=(226, 248, 238), width=2)
        ice_sheet(im, 0, xa, xa + 335, y0 + 40, 13, freeze=fz, crack=cr, breakup=br, hooves=[(xa + 150, 1), (xa + 190, 1)] if k else (),
                  stamps=[(xa + 190, 1.0)] if k >= 2 else ())
        t0, tout = 0.0, 9.0
        tn = (1.2, 4.0, 7.0, 9.6)[k]
        breath(im, tn, xa + 120, y0 + 200, t0, tout, s=1.2, seed=k, ceiling=y0 + 53 if k in (1, 2) else None, surface=y0 + 40 if k in (0, 3) else None,
               release=None)
        d.polygon([(xa + 80, y0 + 196), (xa + 120, y0 + 190), (xa + 122, y0 + 208), (xa + 80, y0 + 214)], fill=(232, 196, 142))
    im.save(path)
    return path


def _sheet_reels(path):
    """Every reel, numbered, lid to the lamp, with the whole frame it holds beside it (a look-up, not film)."""
    cols, cw, ch = 6, 240, 100
    rowsn = (N_REELS + cols - 1) // cols
    im = Image.new("RGB", (cols * cw, rowsn * ch), (60, 48, 86))
    d = ImageDraw.Draw(im)
    for n in range(N_REELS):
        x, y = (n % cols) * cw, (n // cols) * ch
        reel(im, n, x + 50, y + 50, 1.8, paw=n in (0, 12))
        im.paste(frame(n).resize((128, 72)), (x + 104, y + 8))
        reel(im, n, x + 122, y + 90, 0.6)
        reel(im, n, x + 160, y + 90, 0.6, tilt=0.45)
        d = ImageDraw.Draw(im)
        d.text((x + 4, y + 2), str(n), fill=(255, 240, 180))
    im.save(path)
    return path


def _strip(path, cells, cell=(240, 200), kind="water"):
    im = Image.new("RGB", (cell[0] * len(cells), cell[1]))
    for k, fn in enumerate(cells):
        c = _ground(kind, cell)
        fn(c)
        im.paste(c, (k * cell[0], 0))
    im.save(path)
    return path


def _selftest():
    assert len(REELS) == 53 and all((PROJECT / "assets" / r[0]).exists() or frame_path(i).exists() for i, r in enumerate(REELS))
    files = [r[0] for r in REELS]
    order = []                                                   # films stay in the order of WHAT_WE_MADE.md
    for f in files:
        if not order or order[-1] != f:
            order.append(f)
    assert len(order) == len(set(order)), "a film's reels must sit together"
    im = Image.new("RGB", (400, 300), (40, 90, 100))
    out = reel_piles(im, 20, 380, 280, 53)
    assert len(out) == 53 and len({n for _, _, n in out}) == 53
    assert len(reel_piles(im, 20, 380, 280, 7)) == 7
    assert len(pile(im, 5.0, 20, 200, 5, born=[1, 2, 3, 4, 4.9])) == 5
    # the breath does run out: bubbles at the start, none long after the last one
    plan = _breath_plan(8.0, 0, 1.0)
    assert plan[-1][0] == 8.0 and plan[-1][0] - plan[-2][0] > 0.9
    a = Image.new("RGB", (200, 300), (40, 90, 100))
    b = a.copy()
    assert breath(a, 1.0, 100, 280, 0.0, 8.0) > 0.8 and a.tobytes() != b.tobytes()
    a2 = b.copy()
    assert breath(a2, 30.0, 100, 280, 0.0, 8.0) == 0.0 and a2.tobytes() == b.tobytes()
    # a page never bends: carried flat, its four edges stay straight (the sprite is a parallelogram of paper)
    sp = page_sprite("jaw", 1.0, flat=0.86)
    assert sp.getbbox() is not None and sp.height < 40
    for fn in (reel_sprite(3, 1.0), part_sprite("gear"), lantern_sprite(1.0), page_sprite("bars"), page_sprite(blank=True)):
        assert fn.mode == "RGBA" and fn.getbbox() is not None
    print("props self-test passed: 53 reels in order, 53 cans in the piles, breath runs out, sprites carry")


if __name__ == "__main__":
    made = build_frames(force="--frames" in sys.argv)
    print(f"frames: {made} cut, {N_REELS} cached in {FRAMES.relative_to(PROJECT)}")
    print("sheet ->", _sheet_main(HERE / "props_sheet.png").name)
    print("sheet ->", _sheet_reels(HERE / "props_reels.png").name)
    _strip(HERE / "props_strip_breath.png",
           [lambda c, tt=tt: (ice_sheet(c, tt, 0, 240, 30, 12) if tt < 6 else None,
                              breath(c, tt, 120, 180, 0.0, 8.0, s=1.0, ceiling=42 if tt < 6 else None, release=None, surface=30))
            for tt in (0.4, 1.5, 3.0, 4.5, 5.9, 7.0, 8.15, 9.5)])
    _strip(HERE / "props_strip_ice.png",
           [lambda c, a=a: ice_sheet(c, 0, 0, 240, 60, 14, freeze=a[0], crack=a[1], breakup=a[2], origin=0,
                                     hooves=[(100, a[3]), (140, a[3])], stamps=[(140, a[4])])
            for a in ((0.3, 0, 0, 0, 0), (0.7, 0, 0, 0, 0), (1, 0, 0, 1, 0), (1, 0, 0, 1, 0.5), (1, 0.5, 0, 1, 1), (1, 1, 0.3, 1, 1), (1, 1, 0.7, 0, 1))])
    _strip(HERE / "props_strip_pile.png",
           [lambda c, tt=tt: pile(c, tt, 30, 166, int(tt // 2) + 1, s=1.0, born=[2.0 * q + 1.85 for q in range(12)] if tt % 2 > 1.5 else [2.0 * q - 0.1 for q in range(12)], edge=172)
            for tt in (0.2, 1.9, 2.0, 4.2, 6.2, 8.2, 12.2, 22.2)], kind="dusk")
    _strip(HERE / "props_strip_drip.png",
           [lambda c, tt=tt: part(c, 120, 70, 1.6, "gear", t=tt, drip=0.0, floor=166, angle=tt * 8) for tt in (0.1, 0.4, 0.8, 1.5, 2.5, 3.6, 4.6)], kind="dusk")
    _selftest()
