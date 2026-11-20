"""c25 · THE TROUT THINK · the next friend's pick, then bolts 4, 5 and 6, from the river side looking in.

Board beats (module time):
  R0  0.0 ..  2.5   the pick card "Giant astronaut suit", blue cross pressed and scribbled in, the tin ringed blue
  B4  2.5 ..  8.0   bolt 4 · Probable      "The fish swim next to the astronaut, looking..."   (unsure: the last
                    word is off the edge of the sheet, so what they look at is never shown)
  B5  8.0 ..  9.0   bolt 5 · Plausible     BLANK: an empty lit card and its die face
  B6  9.0 .. 10.0   bolt 6 · Preposterous  BLANK: an empty lit card and its die face

Every cut is the card turned over (world.card_flip, 8 frames). Seen from the river the tin and its porthole are
always in frame and Turkey is panicking behind the glass; only a counted wing-beat sends bubbles out of the seam
and drops the dial on the tin's flank a tick. Fish never cross the porthole glass.
Exposes SECONDS, CAPTIONS, draw(t, ink). The editor draws the captions and may draw the badge again.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402
from kit import W, H, FPS, clamp, ramp, ease, smooth, lerp          # noqa: E402
from PIL import Image, ImageDraw                                      # noqa: E402

SECONDS = 10.0
T_B4, T_B5, T_B6 = 2.5, 8.0, 9.0
FLIP = 1.0 / 3.0                                                      # 8 frames

CAPTIONS = [
    (T_B4 + 0.3, T_B5, "The fish swim next to the astronaut, looking..."),
]


# ------------------------------------------------------------------ shared bits ---

def _beat(u, beats, top=96.0, rest=10.0, dur=0.5):
    """Wing angle for counted beats: up and down once per beat, a small tremble between."""
    v = rest + 4 * abs(math.sin(u * 17))
    for b in beats:
        v = max(v, top * math.sin(math.pi * clamp((u - b) / dur)))
    return v


def _ticks(u, beats, start=3.0):
    return start - sum(ramp(u, b + 0.2, b + 0.3) for b in beats)


def _needle(beats, seconds, start=3.0):
    """Secondary dynamics: the needle goes a little too far and comes back."""
    return w.Follower(lambda u: _ticks(u, beats, start), seconds, f=3.0, zeta=0.35)


def _wattle(beats, seconds):
    return w.Follower(lambda u: 30.0 * math.sin(math.pi * clamp((u - 0.05 - min(beats, key=lambda b: abs(u - b))) / 0.5)),
                      seconds, f=2.2, zeta=0.22)


def _flip_kick(u, amp=10.0):
    """The card has just been turned over: the water in the bowl is thrown once."""
    return amp if u < 0.12 else 0.0


def _puff(ink, tp, u, t0, n, size=9.0, scale=1.0):
    """One wing-beat's bubbles: out of the tin's top seam, rising outside the tin, gone before the next beat."""
    if n and u > t0:
        o = (tp["port"][0] + 60 * scale, tp["port"][1] - 96 * scale)
        w.bubbles(ink, o, u, t0=t0, n=n, size=size, rise=150, spread=22, alpha=1 - ramp(u - t0, 0.8, 1.3))


def _glow_bolt(ink, tp, n=4):
    """Bolt n on the tin's own porthole rim, lit warm (1 at twelve, then clockwise)."""
    r = tp["port_r"] * 1.14
    x, y = w.clock_xy(tp["port"], r, (n - 1) * 60)
    lay = ink.layer()
    for k, a in ((3.6, 60), (2.5, 100), (1.6, 170)):
        rr = tp["port_r"] * 0.13 * k
        lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 214, 120, a))
    ink.paste(lay.img)
    rr = tp["port_r"] * 0.1
    ink.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 240, 190, 240))
    return x, y


def _thump(u, beats):
    """The tin shudders a little on each wing-beat: the panic is seen from outside."""
    return max([0.0] + [math.sin(math.pi * clamp((u - b) / 0.5)) for b in beats])


# ------------------------------------------------------------------ R0 · the pick ---

R0_LEN = T_B4
R0_BEATS = [0.55]                                    # he is panicking behind the visor; the dial stays where the page left it
R0_SLOSH = w.Follower(lambda u: _flip_kick(u, 8.0), R0_LEN + 1, f=1.5, zeta=0.3)
R0_WATTLE = _wattle(R0_BEATS, R0_LEN + 1)
CARD_C = (236, 132)
R0_TIN = ((668, 300), 1.0)


def _card_up(ink, u):
    """The pick card flips up about its own lower edge, then lies flat."""
    f = ease(u, 0.1, 0.5)
    press = ease(u, 0.65, 0.85)
    mark = ramp(u, 0.95, 1.5)
    scr = ramp(u, 1.6, 2.2)
    kw = dict(side="trout", picked="cross", press=press, mark=mark, scribble=scr, initial="N.")
    if f <= 0:
        return None
    if f >= 1:
        return w.pick_card(ink, CARD_C, **kw)
    lay = ink.layer()
    w.pick_card(lay, CARD_C, lift=1 - f, **kw)
    box = (max(0, CARD_C[0] - 240), max(0, CARD_C[1] - 150), CARD_C[0] + 250, CARD_C[1] + 170)
    piece = lay.img.crop(box)
    c = math.sin(f * math.pi / 2)
    hh = max(2, int(piece.height * c))
    piece = piece.resize((piece.width, hh), Image.BILINEAR)
    shade = 0.55 + 0.45 * c
    r, g, b, a = piece.split()
    piece = Image.merge("RGBA", (r.point(lambda v: int(v * shade)), g.point(lambda v: int(v * shade)),
                                 b.point(lambda v: int(v * shade)), a))
    ink.paste(piece, (box[0], box[3] - hh))
    return None


def scene_pick(ink, u):
    c, s = R0_TIN
    sl = R0_SLOSH.at(u)
    w.river_backdrop(ink, u)
    tp = w.tin(ink, c, s, u, mood="panic", wing=_beat(u, R0_BEATS), wattle=R0_WATTLE.at(u), shake=2.5 * _thump(u, R0_BEATS))
    _puff(ink, tp, u, R0_BEATS[0] + 0.2, 0)
    w.gauge(ink, 3.0, *w.tin_dial_xy(tp), r=26, t=u)
    w.walker(ink, 150, 492, 214, flip=True, step=0.0, bowl_bubbles=u, slosh=sl, wave=clamp(abs(sl) / 8),
             phase=u * 3, amp=3)
    # the tin is ringed once in blue: riveted shell, round visor. That is the suit.
    done = ramp(u, 1.0, 1.9)
    if done > 0:
        k = s / 1.35
        w.crayon_ring(ink, c, 322 * k, 196 * k, w.PAL["blue"], done, seed=2, width=7)
    r = _card_up(ink, u)
    if r:
        bx, by = r["buttons"]["cross"]
        if 0.85 <= u < 0.95:
            w.pencil(ink, (r["ring"][0] - 4, r["ring"][1] + 6), 50, lift=1 - ramp(u, 0.85, 0.95))
        elif 0.95 <= u < 1.5 and r["tip"] is not None:
            w.pencil(ink, r["tip"], 50)
        elif 1.5 <= u < 1.6:
            q = ease(u, 1.5, 1.6)                                    # the pencil goes over to the button
            w.pencil(ink, (lerp(r["ring"][0], bx, q), lerp(r["ring"][1], by, q)), 50, lift=math.sin(q * math.pi))
        elif 1.6 <= u < 2.2:
            q = (u - 1.6) / 0.6                                      # and colours it in, zigzag
            w.pencil(ink, (bx - 14 + 28 * q, by + 12 * math.sin(q * 40)), 50)
        elif 2.2 <= u < 2.5:
            q = ease(u, 2.2, 2.5)
            w.pencil(ink, (bx + 16 + 120 * q, by + 90 * q), 50, lift=min(1.0, q * 3))


# ------------------------- B4 · The fish swim next to the astronaut, looking... ---

B4_LEN = T_B5 - T_B4
B4_BEATS = [1.0, 3.4]                                # two beats, two puffs, two ticks: half down to one
B4_NEEDLE = _needle(B4_BEATS, B4_LEN + 1)
B4_WATTLE = _wattle(B4_BEATS, B4_LEN + 1)
B4_PACE = 1.0                                        # strides a second for the walker keeping up on the floor
B4_SLOSH = w.Follower(lambda u: _flip_kick(u) + 6.0 * math.sin(2 * math.pi * B4_PACE * 2 * u), B4_LEN + 1, f=1.5, zeta=0.3)
B4_DRIFT = 38.0                                      # px a second the lock slides past: everyone is going right
# the escort: (x, y, length, phase offset, bob). None of them is ever over the porthole glass.
B4_FISH = [
    (214, 118, 124, 0.0, 7),
    (318, 442, 132, 2.1, 6),
    (566, 478, 118, 4.0, 5),
    (936, 446, 136, 1.2, 6),                         # the lead fish: its eye is already past the right edge of the card
]


def _tin_pose(u):
    """The giant suit hangs slow and weightless: a long bob, a few degrees of tilt."""
    c = (622 + 6 * math.sin(u * 0.7 + 1.0), 236 + 9 * math.sin(u * 0.9))
    return c, 4.0 * math.sin(u * 0.55 + 0.4) + 2.0


def scene_astronaut(ink, u):
    w.river_backdrop(ink, u, shift=104 - B4_DRIFT * u)
    c, ang = _tin_pose(u)
    tp = w.tin(ink, c, 1.35, u, mood="panic", angle=ang, wing=_beat(u, B4_BEATS), wattle=B4_WATTLE.at(u),
               shake=3.0 * _thump(u, B4_BEATS))
    w.gauge(ink, max(0.0, B4_NEEDLE.at(u)), *w.tin_dial_xy(tp), r=34, t=u)
    bx, by = _glow_bolt(ink, tp, 4)
    w.die_face(ink, 4, bx, by + 46, size=42)
    for b in B4_BEATS:
        _puff(ink, tp, u, b + 0.2, 9, size=14.0, scale=1.35)
    # the escort keeps station: each fish holds its place beside the suit and rides the suit's own slow bob
    dx, dy = c[0] - 622, c[1] - 236
    for k, (x, y, ln, ph, bob) in enumerate(B4_FISH):
        fx = x + dx * 0.8 + 5 * math.sin(u * 1.3 + ph)
        fy = y + dy * 0.8 + bob * math.sin(u * 1.1 + ph * 1.7)
        w.trout(ink, fx, fy, ln, angle=2.5 * math.sin(u * 1.1 + ph * 1.7 + 1.2), flip=True, phase=u * 6 + ph, amp=9, lid=0.0)
    sl = B4_SLOSH.at(u)
    w.walker(ink, 122 + dx * 0.8, 500, 150, flip=True, step=u * B4_PACE, bowl_bubbles=u, slosh=sl,
             wave=clamp(abs(sl) / 8), phase=u * 5, amp=5)


# ------------------------------------------------------------ B5, B6 · the blanks ---

def scene_blank5(ink, u):
    w.empty_card(ink)
    w.bolt_die(ink, 5)


def scene_blank6(ink, u):
    w.empty_card(ink)
    w.bolt_die(ink, 6)


# ------------------------------------------------------------------------ the cut ---

SCENES = [(0.0, scene_pick), (T_B4, scene_astronaut), (T_B5, scene_blank5), (T_B6, scene_blank6)]


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    k = max(i for i, (t0, _) in enumerate(SCENES) if t >= t0)
    t0, fn = SCENES[k]
    f = (t - t0) / FLIP
    if k > 0 and f < 1.0:
        # the old card (held on its last frame) is turned over top to bottom; the new scene is on its back
        p0, pfn = SCENES[k - 1]
        pfn(ink, t0 - p0 - 1.0 / FPS)
        o = w.offscreen(ink)
        fn(o, t - t0)
        w.card_flip(ink, o.img, f)
    else:
        fn(ink, t - t0)
    w.badge(ink)


# ------------------------------------------------------------------- test harness ---

if __name__ == "__main__":
    from kit import Film

    out = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("/tmp/c25_scene_trout")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in sys.argv[2:] if not a.startswith("--")] or [
        0.1, 0.35, 0.8, 1.3, 1.9, 2.4, 2.62, 2.9, 3.6, 3.9, 4.6, 5.4, 6.1, 6.6, 7.3, 7.9, 8.12, 8.6, 9.12, 9.7]
    captions = "--captions" in sys.argv
    film = Film("c25_scene_trout", SECONDS)

    def frame(t, ink):
        draw(t, ink)
        if captions:
            for a, b, text in CAPTIONS:
                if a <= t < b:
                    ink.caption(text, size=27)
    film.picture(frame)
    frames = []
    for tt in times:
        im = film.frame(int(round(tt * film.fps)))
        im.save(out / f"{tt:06.2f}.png")
        frames.append(im)
    cols = 4
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 20))
    for i, im in enumerate(frames):
        sheet.paste(im.resize((480, 270), Image.LANCZOS), ((i % cols) * 480, (i // cols) * 270))
        ImageDraw.Draw(sheet).text(((i % cols) * 480 + 6, (i // cols) * 270 + 4), f"{times[i]:.2f}", fill=(255, 255, 0))
    sheet.save(out / "sheet.png")
    print("wrote", out / "sheet.png")
